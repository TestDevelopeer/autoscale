"""Модели данных лицензии."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    GRACE = "grace"
    OFFLINE_VALID = "offline_valid"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    MACHINE_MISMATCH = "machine_mismatch"
    MISSING = "missing"
    INVALID = "invalid"


MVP_MODULES = frozenset({
    "core",
    "terminals",
    "cameras",
    "alpr",
    "weighing_journal",
    "drivers_registry",
    "workplaces",
    "reports_basic",
    "api_access",
    "multi_workplace",
})


class LicenseLimits(BaseModel):
    max_users: int = 5
    max_workplaces: int = 1
    max_terminals: int = 2
    max_cameras: int = 4
    max_records_per_month: int = 0


class LicensePayload(BaseModel):
    format_version: int = 1
    license_id: UUID
    client_id: UUID
    organization_name: str = ""
    modules: list[str] = Field(default_factory=lambda: ["core"])
    limits: LicenseLimits = Field(default_factory=LicenseLimits)
    expires_at: datetime
    grace_days: int = 14
    offline_until: datetime | None = None
    machine_fingerprint: str
    issued_at: datetime
    status: LicenseStatus = LicenseStatus.ACTIVE

    def has_module(self, module: str) -> bool:
        return module in self.modules


class SignedLicenseFile(BaseModel):
    payload: LicensePayload
    signature: str


class ActivationRequest(BaseModel):
    format_version: int = 1
    request_id: UUID
    machine_fingerprint: str
    product_version: str = "0.1.0"
    requested_at: datetime
    hostname: str = ""


class ValidationResult(BaseModel):
    valid: bool
    status: LicenseStatus
    message: str
    payload: LicensePayload | None = None
    user_message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
