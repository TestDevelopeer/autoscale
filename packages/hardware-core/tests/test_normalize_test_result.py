"""Тесты normalize_test_result."""

from __future__ import annotations

from decimal import Decimal

from hardware_core.terminal import TerminalReading, TestResult, normalize_test_result


def test_normalize_sets_connected_when_success_with_reading():
    reading = TerminalReading(
        weight=Decimal("15000"),
        unit="kg",
        stable=True,
        raw="ST 00015000",
        status="ok",
    )
    result = TestResult(success=True, message="ok", sample_reading=reading, connected=False)
    normalized = normalize_test_result(result)
    assert normalized.connected is True


def test_normalize_legacy_keli_frame_st_00015000():
    from terminal_drivers.keli_d2008fa.parser import parse_keli_modbus_response

    reading = parse_keli_modbus_response("ST 00015000")
    assert str(reading.weight) == "15000"
    assert reading.stable is True
    assert reading.unit == "kg"
    assert reading.raw == "ST 00015000"

    result = normalize_test_result(
        TestResult(success=True, sample_reading=reading, connected=False)
    )
    assert result.connected is True


def test_normalize_keeps_connected_false_on_failure():
    reading = TerminalReading(
        weight=Decimal("0"),
        raw="???",
        status="parse_error",
        error="parse error",
    )
    result = TestResult(
        success=False,
        connected=True,
        error_code="parse_failed",
        sample_reading=reading,
    )
    normalized = normalize_test_result(result)
    assert normalized.connected is True
    assert normalized.success is False
