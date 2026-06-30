"""Keli D2008FA driver — реальное чтение COM при указанном port в config."""

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
from terminal_drivers.keli_d2008fa.serial_session import (
    read_keli_frame_once,
    read_keli_reading,
    serial_settings_from_config,
    probe_keli_hardware,
    probe_keli_on_serial,
)
from terminal_drivers.probe.serial_io import PortProbeError, open_serial


class KeliD2008faDriver:
    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._connected = False
        self._last_reading: TerminalReading | None = None
        self._ser = None
        self._settings = None

    def connect(self) -> None:
        port = self._config.get("port")
        if not port:
            self._connected = False
            return
        try:
            self._settings = serial_settings_from_config(self._config)
            self._ser = open_serial(self._settings)
            self._connected = True
        except (PortProbeError, ImportError):
            self._connected = False
            self._ser = None

    def disconnect(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._connected = False

    def test_connection(self) -> TestResult:
        if not self._config.get("port"):
            return TestResult(
                success=False,
                connected=False,
                message="Для Keli D2008FA укажите COM-порт",
                error_code="port_required",
            )
        if self._ser is not None and self._connected and self._settings is not None:
            return probe_keli_on_serial(self._ser, self._settings)
        return probe_keli_hardware(self._config)

    def read_frame(self) -> str:
        if self._ser is not None and self._settings is not None:
            raw = read_keli_frame_once(self._ser, self._settings)
            if raw:
                return raw.decode("ascii", errors="ignore")
            return ""
        return ""

    def parse_frame(self, raw: bytes | str) -> TerminalReading:
        reading = parse_keli_modbus_response(raw)
        self._last_reading = reading
        return reading

    def get_current_weight(self) -> TerminalReading:
        if self._ser is not None and self._connected:
            reading = read_keli_reading(self._config, self._ser)
            if reading is not None:
                self._last_reading = reading
                return reading
        if self._last_reading:
            return self._last_reading
        return TerminalReading(
            weight=0,
            unit="kg",
            stable=False,
            raw="",
            status="no_data",
            error="Нет данных с терминала Keli",
            protocol="keli_modbus",
        )

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
