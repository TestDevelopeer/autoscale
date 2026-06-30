"""Общая логика лицензий: подпись, проверка, fingerprint, modules."""

from license_core.fingerprint import collect_machine_fingerprint
from license_core.models import LicenseLimits, LicensePayload, LicenseStatus, SignedLicenseFile
from license_core.validator import LicenseValidator, ValidationResult

__all__ = [
    "LicenseLimits",
    "LicensePayload",
    "LicenseStatus",
    "SignedLicenseFile",
    "LicenseValidator",
    "ValidationResult",
    "collect_machine_fingerprint",
]
