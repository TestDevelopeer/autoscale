from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest
from license_core.models import LicenseLimits, LicensePayload, LicenseStatus, SignedLicenseFile
from license_core.validator import LicenseSigner, LicenseValidator, generate_keypair

from app.services.workplace_orchestrator import WorkplaceConfig, WorkplaceOrchestrator, WeighingState
from hardware_core.terminal import TerminalReading
from alpr_core import normalize_ru_plate
from terminal_drivers import parse_cas_frame, parse_keli_modbus_response


def test_normalize_ru_plate_homoglyphs():
    assert normalize_ru_plate("А123ВС77") == "A123BC77"


def test_keli_parser():
    reading = parse_keli_modbus_response("ST 00015000")
    assert reading.weight == Decimal("15000")
    assert reading.protocol == "keli_modbus"


def test_cas_parser():
    reading = parse_cas_frame("ST     15230 kg")
    assert reading.weight == Decimal("15230")
    assert reading.stable is True


def test_license_sign_and_verify():
    priv, pub = generate_keypair()
    signer = LicenseSigner(priv)
    validator = LicenseValidator(pub)
    fp = "sha256:test"
    payload = LicensePayload(
        license_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        modules=["core", "terminals"],
        limits=LicenseLimits(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        machine_fingerprint=fp,
        issued_at=datetime.now(timezone.utc),
        status=LicenseStatus.ACTIVE,
    )
    signed = signer.sign(payload)
    result = validator.validate(signed, current_fingerprint=fp)
    assert result.valid
    assert result.status == LicenseStatus.ACTIVE


def test_fsm_idle_to_vehicle_detected():
    config = WorkplaceConfig(min_weight_threshold=Decimal("100"), stable_seconds=0.1, alpr_enabled=False)
    orch = WorkplaceOrchestrator(config)
    orch.reset("wp-1")
    reading = TerminalReading(weight=Decimal("5000"), stable=False, raw="test")
    state = orch.on_weight(reading)
    assert state in (WeighingState.VEHICLE_DETECTED, WeighingState.WEIGHT_WAITING)
