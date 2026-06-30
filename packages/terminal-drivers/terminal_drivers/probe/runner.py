"""Запуск hardware probe сессии."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from hardware_core.terminal import TerminalReading

from terminal_drivers.cas_ci200a.parser import parse_cas_frame
from terminal_drivers.keli_d2008fa.parser import parse_keli_modbus_response
from terminal_drivers.probe.errors import (
    ProbeDiagnostic,
    no_stable_flag,
    parse_failed,
    terminal_silent,
    unstable_weight,
)
from terminal_drivers.probe.report import ProbeReport
from terminal_drivers.probe.serial_io import (
    PortProbeError,
    SerialSettings,
    cas_command_wt,
    keli_poll_frame,
    open_serial,
    read_available,
)


DRIVER_ALIASES = {
    "keli-d2008fa": "keli_d2008fa",
    "keli_d2008fa": "keli_d2008fa",
    "cas-ci-200a": "cas_ci200a",
    "cas_ci200a": "cas_ci200a",
    "demo": "demo",
}


def normalize_driver_name(name: str) -> str:
    key = name.strip().lower()
    if key not in DRIVER_ALIASES:
        raise ValueError(f"Неизвестный драйвер: {name}. Допустимо: keli-d2008fa, cas-ci-200a, demo")
    return DRIVER_ALIASES[key]


def _reading_to_dict(reading: TerminalReading) -> dict:
    data = reading.model_dump(mode="json")
    data["timestamp"] = reading.timestamp.isoformat() if reading.timestamp else None
    return data


def _parse_frame(driver: str, raw: bytes | str) -> TerminalReading:
    if driver == "keli_d2008fa":
        return parse_keli_modbus_response(raw)
    if driver == "cas_ci200a":
        return parse_cas_frame(raw)
    raise ValueError(driver)


def _evaluate_reading(reading: TerminalReading, report: ProbeReport) -> None:
    if reading.status != "ok" or reading.error:
        report.add_error({
            **parse_failed(str(reading.raw)[:120]).to_dict(),
            "parser_error": reading.error,
        })
        return

    report.record_success()
    report.add_parsed(_reading_to_dict(reading))

    if not reading.stable:
        report.add_warning(unstable_weight(str(reading.weight)).to_dict())
        if "ST" not in str(reading.raw).upper():
            report.add_warning(no_stable_flag().to_dict())


class TerminalProbeRunner:
    """Чтение терминала без записи в журнал и без FSM."""

    def __init__(self, driver: str, settings: SerialSettings) -> None:
        self.driver = normalize_driver_name(driver)
        self.settings = settings

    def run(self, duration: float = 10.0, poll_interval: float = 0.2) -> ProbeReport:
        started = datetime.now(timezone.utc)
        report = ProbeReport(
            driver=self.driver,
            port_settings=self.settings.to_dict(),
            started_at=started.isoformat(),
            duration=duration,
        )

        if self.driver == "demo":
            self._run_demo(report, duration, poll_interval)
            report.duration = duration
            report.finalize()
            return report

        try:
            ser = open_serial(self.settings)
        except PortProbeError as exc:
            report.add_error(exc.diagnostic.to_dict())
            report.duration = 0.0
            report.finalize()
            return report
        except ImportError as exc:
            report.add_error({
                "code": "serial_unavailable",
                "message": str(exc),
                "hint": "pip install pyserial",
            })
            report.duration = 0.0
            report.finalize()
            return report

        report.connected = True
        deadline = time.monotonic() + duration
        silent_start = time.monotonic()

        try:
            with ser:
                while time.monotonic() < deadline:
                    raw = self._read_once(ser)
                    if raw:
                        silent_start = time.monotonic()
                        report.add_raw(raw)
                        reading = _parse_frame(self.driver, raw)
                        _evaluate_reading(reading, report)
                    elif time.monotonic() - silent_start >= self.settings.timeout:
                        report.add_error(terminal_silent(self.settings.port, self.settings.timeout).to_dict())
                        silent_start = time.monotonic()
                    time.sleep(poll_interval)
        except PortProbeError as exc:
            report.add_error(exc.diagnostic.to_dict())

        report.duration = duration
        report.finalize()
        return report

    def _read_once(self, ser) -> bytes:
        if self.driver == "keli_d2008fa":
            ser.write(keli_poll_frame(self.settings))
            ser.flush()
            time.sleep(0.05)
            return read_available(ser)
        if self.driver == "cas_ci200a":
            chunk = read_available(ser)
            if chunk:
                return chunk
            ser.write(cas_command_wt())
            ser.flush()
            time.sleep(0.1)
            return read_available(ser)
        return b""

    def _run_demo(self, report: ProbeReport, duration: float, poll_interval: float) -> None:
        from terminal_drivers.demo.driver import DemoTerminalDriver

        driver = DemoTerminalDriver({
            "target_weight": 15000,
            "ramp_seconds": 1.0,
            "stable_after": 2.0,
        })
        driver.connect()
        report.connected = True
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            reading = driver.get_current_weight()
            report.add_raw(reading.raw)
            _evaluate_reading(reading, report)
            time.sleep(poll_interval)
        driver.disconnect()

    def run_fixture(self, frames: list[bytes | str], duration: float = 0.0) -> ProbeReport:
        """Режим без COM — для unit-тестов и отладки parser."""
        started = datetime.now(timezone.utc)
        report = ProbeReport(
            driver=self.driver,
            port_settings=self.settings.to_dict(),
            started_at=started.isoformat(),
            duration=duration or len(frames) * 0.2,
            connected=False,
        )
        for frame in frames:
            report.add_raw(frame)
            reading = _parse_frame(self.driver, frame)
            _evaluate_reading(reading, report)
        report.finalize()
        return report
