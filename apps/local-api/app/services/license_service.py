"""Сервис лицензирования."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from license_core import LicenseValidator, collect_machine_fingerprint
from license_core.models import ActivationRequest, LicensePayload, LicenseStatus, SignedLicenseFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import AuditLog, LicenseState


class LicenseService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fingerprint = collect_machine_fingerprint()
        self._validator: LicenseValidator | None = None
        if settings.license_public_key:
            self._validator = LicenseValidator(settings.license_public_key)

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def _load_signed_file(self) -> SignedLicenseFile | None:
        path = Path(self._settings.license_file_path)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return SignedLicenseFile.model_validate(data)

    def _save_signed_file(self, signed: SignedLicenseFile) -> None:
        path = Path(self._settings.license_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(signed.model_dump_json(indent=2), encoding="utf-8")

    async def get_status(self, db: AsyncSession) -> dict:
        signed = self._load_signed_file()
        result = await db.scalar(select(LicenseState).where(LicenseState.id == 1))

        if signed is None or self._validator is None:
            return {
                "status": LicenseStatus.MISSING.value,
                "valid": False,
                "user_message": "Лицензия не активирована.",
                "machine_fingerprint": self._fingerprint,
                "modules": [],
                "limits": {},
            }

        validation = self._validator.validate(
            signed,
            current_fingerprint=self._fingerprint,
            last_validated_at=result.last_validated_at if result else None,
        )

        return {
            "status": validation.status.value,
            "valid": validation.valid,
            "user_message": validation.user_message,
            "machine_fingerprint": self._fingerprint,
            "modules": signed.payload.modules if validation.payload else [],
            "limits": signed.payload.limits.model_dump() if validation.payload else {},
            "expires_at": signed.payload.expires_at.isoformat() if validation.payload else None,
            "license_id": str(signed.payload.license_id) if validation.payload else None,
        }

    async def import_license(self, db: AsyncSession, signed: SignedLicenseFile, user_id: uuid.UUID | None = None) -> dict:
        if self._validator is None:
            raise ValueError("LICENSE_PUBLIC_KEY не настроен")

        validation = self._validator.validate(signed, current_fingerprint=self._fingerprint)
        if not validation.valid:
            raise ValueError(validation.user_message)

        self._save_signed_file(signed)
        state = await db.scalar(select(LicenseState).where(LicenseState.id == 1))
        if state is None:
            state = LicenseState(id=1)
            db.add(state)

        state.license_id = signed.payload.license_id
        state.status = validation.status.value
        state.raw_file = signed.model_dump_json()
        state.last_validated_at = datetime.now(timezone.utc)
        state.monotonic_counter += 1

        db.add(AuditLog(action="license.import", user_id=user_id, details={"license_id": str(signed.payload.license_id)}))
        await db.commit()
        return await self.get_status(db)

    async def create_offline_request(self) -> dict:
        req = ActivationRequest(
            request_id=uuid.uuid4(),
            machine_fingerprint=self._fingerprint,
            requested_at=datetime.now(timezone.utc),
            hostname=__import__("socket").gethostname(),
        )
        return req.model_dump(mode="json")

    async def activate_online(
        self,
        db: AsyncSession,
        license_id: str,
        activation_code: str,
        user_id: uuid.UUID | None = None,
    ) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._settings.owner_admin_url}/api/licenses/activate",
                json={
                    "license_id": license_id,
                    "activation_code": activation_code,
                    "machine_fingerprint": self._fingerprint,
                },
            )
            response.raise_for_status()
            signed = SignedLicenseFile.model_validate(response.json())

        return await self.import_license(db, signed, user_id)

    def require_module(self, module: str) -> None:
        signed = self._load_signed_file()
        if signed is None or self._validator is None:
            raise PermissionError("Лицензия не активирована")
        validation = self._validator.validate(signed, current_fingerprint=self._fingerprint)
        if not validation.valid:
            raise PermissionError(validation.user_message)
        if not signed.payload.has_module(module):
            raise PermissionError(f"Модуль '{module}' не включён в лицензию")
