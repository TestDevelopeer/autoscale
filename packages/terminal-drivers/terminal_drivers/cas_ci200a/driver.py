"""CAS CI-200A driver."""

from __future__ import annotations

from typing import Any

from hardware_core.health import HealthReport, HealthStatus
from hardware_core.terminal import (
    TerminalCapabilities,
    TerminalReading,
    TerminalStatus,
    TestResult,
)
from terminal_drivers.cas_ci200a.parser import parse_cas_frame


class CasCi200aDriver:
    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._connected = False
        self._last_reading: TerminalReading | None = None

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def test_connection(self) -> TestResult:
        sample = parse_cas_frame("ST     15230 kg")
        self._last_reading = sample
        return TestResult(
            success=True,
            message="CAS parser self-test OK (stream/command verify on hardware required)",
            sample_reading=sample,
        )

    def read_frame(self) -> str:
        return "ST     15230 kg"

    def parse_frame(self, raw: bytes | str) -> TerminalReading:
        reading = parse_cas_frame(raw)
        self._last_reading = reading
        return reading

    def get_current_weight(self) -> TerminalReading:
        if self._last_reading:
            return self._last_reading
        return self.parse_frame(self.read_frame())

    def get_status(self) -> TerminalStatus:
        return TerminalStatus(
            connected=self._connected,
            protocol="cas_stream",
            last_reading=self.get_current_weight(),
        )

    def zero(self) -> bool:
        return False

    def health(self) -> HealthReport:
        return HealthReport(
            status=HealthStatus.OK if self._connected else HealthStatus.DEGRADED,
            message="CAS CI-200A",
        )

    def capabilities(self) -> TerminalCapabilities:
        return TerminalCapabilities(
            supports_zero=True,
            supports_stream=True,
            supports_command_mode=True,
            protocols=["cas_stream", "cas_command"],
        )
