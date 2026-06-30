"""Keli D2008FA driver (Modbus polling — MVP без реального COM в dev)."""

from __future__ import annotations

from typing import Any

from hardware_core.health import HealthReport, HealthStatus
from hardware_core.terminal import (
    TerminalCapabilities,
    TerminalReading,
    TerminalStatus,
    TestResult,
)
from terminal_drivers.keli_d2008fa.parser import parse_keli_modbus_response


class KeliD2008faDriver:
    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._connected = False
        self._last_reading: TerminalReading | None = None

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def test_connection(self) -> TestResult:
        # Без реального COM возвращаем структурный успех для конфигурации
        sample = parse_keli_modbus_response("ST 00015000")
        self._last_reading = sample
        return TestResult(
            success=True,
            message="Keli parser self-test OK (COM verify on hardware required)",
            sample_reading=sample,
        )

    def read_frame(self) -> str:
        return "ST 00015000"

    def parse_frame(self, raw: bytes | str) -> TerminalReading:
        reading = parse_keli_modbus_response(raw)
        self._last_reading = reading
        return reading

    def get_current_weight(self) -> TerminalReading:
        if self._last_reading:
            return self._last_reading
        return self.parse_frame(self.read_frame())

    def get_status(self) -> TerminalStatus:
        return TerminalStatus(
            connected=self._connected,
            protocol="keli_modbus",
            last_reading=self.get_current_weight(),
        )

    def zero(self) -> bool:
        return False

    def health(self) -> HealthReport:
        return HealthReport(
            status=HealthStatus.OK if self._connected else HealthStatus.DEGRADED,
            message="Keli D2008FA",
        )

    def capabilities(self) -> TerminalCapabilities:
        return TerminalCapabilities(
            supports_zero=False,
            supports_stream=False,
            supports_command_mode=True,
            protocols=["keli_modbus"],
        )
