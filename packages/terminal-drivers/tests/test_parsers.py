from decimal import Decimal

import pytest

from terminal_drivers import parse_cas_frame, parse_keli_modbus_response
from terminal_drivers.probe.report import ProbeReport
from terminal_drivers.probe.runner import TerminalProbeRunner, normalize_driver_name
from terminal_drivers.probe.serial_io import SerialSettings


def test_keli_parser_weight():
    reading = parse_keli_modbus_response("ST 00015000")
    assert reading.weight == Decimal("15000")
    assert reading.stable is True
    assert reading.status == "ok"


def test_keli_parser_unstable():
    reading = parse_keli_modbus_response("US 00015000")
    assert reading.weight == Decimal("15000")
    assert reading.stable is False


def test_keli_parser_error():
    reading = parse_keli_modbus_response("??? no digits")
    assert reading.status == "parse_error"
    assert reading.error


def test_cas_parser_stable():
    reading = parse_cas_frame("ST     15230 kg")
    assert reading.stable is True
    assert reading.weight == Decimal("15230")


def test_cas_parser_unstable():
    reading = parse_cas_frame("US     12000 kg")
    assert reading.weight == Decimal("12000")
    assert reading.stable is False


def test_cas_parser_error():
    reading = parse_cas_frame("no weight")
    assert reading.status == "parse_error"


def test_normalize_driver_aliases():
    assert normalize_driver_name("keli-d2008fa") == "keli_d2008fa"
    assert normalize_driver_name("cas-ci-200a") == "cas_ci200a"


def test_probe_report_format_and_save(tmp_path):
    report = ProbeReport(
        driver="keli_d2008fa",
        port_settings={"port": "COM3"},
        started_at="2026-01-01T00:00:00+00:00",
        duration=1.0,
        connected=True,
    )
    report.record_success()
    report.finalize()
    path = tmp_path / "probe.json"
    report.save(path)
    data = path.read_text(encoding="utf-8")
    assert "success_count" in data
    assert "recommended_next_action" in data


def test_probe_fixture_keli():
    settings = SerialSettings(port="FIXTURE", baudrate=9600)
    runner = TerminalProbeRunner("keli-d2008fa", settings)
    report = runner.run_fixture(["ST 00015000", "garbage"])
    assert report.success_count >= 1
    assert report.failure_count >= 1


def test_probe_demo_mode():
    settings = SerialSettings(port="DEMO", baudrate=0)
    runner = TerminalProbeRunner("demo", settings)
    report = runner.run(duration=2.5, poll_interval=0.2)
    assert report.connected
    assert report.success_count >= 1


def test_unknown_driver():
    with pytest.raises(ValueError, match="Неизвестный"):
        normalize_driver_name("unknown")
