"""Подпись и проверка license file (Ed25519)."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from license_core.canonical import canonical_json_bytes
from license_core.models import LicensePayload, LicenseStatus, SignedLicenseFile, ValidationResult


class LicenseSigner:
    """Подпись license file (только owner-admin)."""

    def __init__(self, private_key_b64: str) -> None:
        key_bytes = base64.b64decode(private_key_b64)
        self._private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)

    def sign(self, payload: LicensePayload) -> SignedLicenseFile:
        payload_dict = payload.model_dump(mode="json")
        signature = self._private_key.sign(canonical_json_bytes(payload_dict))
        return SignedLicenseFile(
            payload=payload,
            signature=base64.b64encode(signature).decode("ascii"),
        )


class LicenseValidator:
    """Проверка подписи, срока, fingerprint и modules."""

    def __init__(self, public_key_b64: str) -> None:
        key_bytes = base64.b64decode(public_key_b64)
        self._public_key = Ed25519PublicKey.from_public_bytes(key_bytes)

    def verify_signature(self, signed: SignedLicenseFile) -> bool:
        payload_dict = signed.payload.model_dump(mode="json")
        try:
            self._public_key.verify(
                base64.b64decode(signed.signature),
                canonical_json_bytes(payload_dict),
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    def validate(
        self,
        signed: SignedLicenseFile,
        *,
        current_fingerprint: str,
        now: datetime | None = None,
        last_validated_at: datetime | None = None,
    ) -> ValidationResult:
        now = now or datetime.now(timezone.utc)

        if signed.payload.status in (LicenseStatus.REVOKED, LicenseStatus.SUSPENDED):
            return ValidationResult(
                valid=False,
                status=signed.payload.status,
                message=f"License {signed.payload.status.value}",
                payload=signed.payload,
                user_message="Лицензия недоступна. Обратитесь к поставщику.",
            )

        if not self.verify_signature(signed):
            return ValidationResult(
                valid=False,
                status=LicenseStatus.INVALID,
                message="Invalid signature",
                user_message="Файл лицензии повреждён или изменён.",
            )

        if signed.payload.machine_fingerprint != current_fingerprint:
            return ValidationResult(
                valid=False,
                status=LicenseStatus.MACHINE_MISMATCH,
                message="Fingerprint mismatch",
                payload=signed.payload,
                user_message="Лицензия привязана к другому компьютеру.",
            )

        if last_validated_at and now < last_validated_at:
            return ValidationResult(
                valid=False,
                status=LicenseStatus.INVALID,
                message="Clock rollback detected",
                user_message="Обнаружен откат системного времени.",
            )

        expires = signed.payload.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if now > expires:
            grace_end = expires.replace()  # copy
            from datetime import timedelta

            grace_end = expires + timedelta(days=signed.payload.grace_days)
            if now <= grace_end:
                return ValidationResult(
                    valid=True,
                    status=LicenseStatus.GRACE,
                    message="License in grace period",
                    payload=signed.payload,
                    user_message="Лицензия истекла, действует льготный период.",
                )
            return ValidationResult(
                valid=False,
                status=LicenseStatus.EXPIRED,
                message="License expired",
                payload=signed.payload,
                user_message="Срок действия лицензии истёк.",
            )

        return ValidationResult(
            valid=True,
            status=LicenseStatus.ACTIVE,
            message="License valid",
            payload=signed.payload,
            user_message="Лицензия активна.",
        )

    def has_module(self, signed: SignedLicenseFile | None, module: str) -> bool:
        if signed is None:
            return False
        result = self.validate(signed, current_fingerprint=signed.payload.machine_fingerprint)
        return result.valid and signed.payload.has_module(module)


def generate_keypair() -> tuple[str, str]:
    """Генерация Ed25519 keypair для dev/setup."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    priv_b64 = base64.b64encode(private_key.private_bytes_raw()).decode("ascii")
    pub_b64 = base64.b64encode(public_key.public_bytes_raw()).decode("ascii")
    return priv_b64, pub_b64
