"""Дополнительные тесты приёмки MVP."""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from license_core.canonical import canonical_json_bytes
from license_core.models import LicenseLimits, LicensePayload, LicenseStatus
from license_core.validator import LicenseSigner, LicenseValidator, generate_keypair
from license_core.fingerprint import collect_machine_fingerprint

from alpr_core import normalize_ru_plate
from app.services.workplace_orchestrator import WorkplaceConfig, WorkplaceOrchestrator, WeighingState
from hardware_core.terminal import TerminalReading


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("А123ВС161", "A123BC161"),
        ("A123BC161", "A123BC161"),
        ("А 123 ВС 161", "A123BC161"),
        ("X777XX77", "X777XX77"),
        ("Х777ХХ77", "X777XX77"),
        ("А123ВС77", "A123BC77"),
    ],
)
def test_plate_normalization_matrix(raw: str, expected: str):
    assert normalize_ru_plate(raw) == expected


def test_fsm_demo_path_to_ready():
    config = WorkplaceConfig(
        min_weight_threshold=Decimal("100"),
        stable_seconds=0.0,
        max_weight_delta=Decimal("100"),
        alpr_enabled=False,
    )
    orch = WorkplaceOrchestrator(config)
    orch.reset("wp-demo")

    reading = TerminalReading(weight=Decimal("15000"), stable=True, raw="demo")
    for _ in range(5):
        orch.on_weight(reading)

    assert orch.context.state == WeighingState.READY_TO_CAPTURE
    orch.capture()
    assert orch.context.state == WeighingState.CAPTURED


def test_license_php_python_compatible():
    priv, pub = generate_keypair()
    payload = LicensePayload(
        license_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        client_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
        organization_name="Test Org",
        modules=["core", "terminals", "alpr"],
        limits=LicenseLimits(max_terminals=5),
        expires_at=datetime(2027, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        machine_fingerprint="sha256:testfp",
        issued_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        status=LicenseStatus.ACTIVE,
    )
    payload_dict = payload.model_dump(mode="json")
    canonical_py = canonical_json_bytes(payload_dict)

    php_root = Path(__file__).resolve().parents[2] / "owner-admin"
    php_script = """
<?php
require __DIR__ . '/vendor/autoload.php';
use App\\Support\\LicenseCanonicalJson;
$payload = json_decode(file_get_contents('php://stdin'), true);
echo LicenseCanonicalJson::encode($payload);
"""
    proc = subprocess.run(
        ["php", "-r", php_script],
        input=json.dumps(payload_dict),
        capture_output=True,
        text=True,
        cwd=str(php_root),
        check=False,
    )
    if proc.returncode != 0:
        pytest.skip(f"PHP unavailable or owner-admin not bootstrapped: {proc.stderr}")

    canonical_php = proc.stdout.encode("utf-8")
    assert canonical_py == canonical_php

    signer = LicenseSigner(priv)
    signed = signer.sign(payload)
    validator = LicenseValidator(pub)
    result = validator.validate(signed, current_fingerprint="sha256:testfp")
    assert result.valid


def test_require_module_blocks_without_license(tmp_path):
    from app.config import Settings
    from app.services.license_service import LicenseService

    priv, pub = generate_keypair()
    signer = LicenseSigner(priv)
    payload = LicensePayload(
        license_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        modules=["core"],
        limits=LicenseLimits(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        machine_fingerprint=collect_machine_fingerprint(),
        issued_at=datetime.now(timezone.utc),
        status=LicenseStatus.ACTIVE,
    )
    signed = signer.sign(payload)
    license_path = tmp_path / "license.lic"
    license_path.write_text(signed.model_dump_json(), encoding="utf-8")

    settings = Settings(license_public_key=pub, license_file_path=str(license_path))
    service = LicenseService(settings)
    with pytest.raises(PermissionError, match="terminals"):
        service.require_module("terminals")
