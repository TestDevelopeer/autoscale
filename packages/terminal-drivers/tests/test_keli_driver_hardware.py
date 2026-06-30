"""Тесты Keli driver с mock serial (без физического COM)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from terminal_drivers.factory import create_terminal_driver
from terminal_drivers.keli_d2008fa.serial_session import (
    serial_settings_from_config,
    probe_keli_hardware,
    probe_keli_on_serial,
)
from terminal_drivers.probe.errors import port_access_denied, port_not_found
from terminal_drivers.probe.serial_io import PortProbeError, SerialSettings


KELI_CONFIG = {
    "port": "COM1",
    "baudrate": 9600,
    "parity": "none",
    "timeout": 2,
}

LEGACY_FRAME = b"ST 00015000"
REAL_FRAME = b"ST,GS,+0000000kg"


def test_serial_settings_from_config_maps_parity_none():
    settings = serial_settings_from_config(KELI_CONFIG)
    assert settings.port == "COM1"
    assert settings.baudrate == 9600
    assert settings.parity == "none"
    assert settings.timeout == 2.0


def test_keli_driver_is_not_demo():
    driver = create_terminal_driver("keli_d2008fa", KELI_CONFIG)
    assert driver.__class__.__name__ == "KeliD2008faDriver"


@patch("terminal_drivers.keli_d2008fa.serial_session.open_serial")
def test_keli_hardware_reads_legacy_frame(mock_open_serial):
    ser = MagicMock()
    mock_open_serial.return_value = ser

    with patch(
        "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
        return_value=LEGACY_FRAME,
    ):
        result = probe_keli_hardware(KELI_CONFIG)

    assert result.success is True
    assert result.connected is True
    assert result.sample_reading is not None
    assert str(result.sample_reading.weight) == "15000"
    assert result.sample_reading.stable is True
    assert result.sample_reading.unit == "kg"
    assert result.sample_reading.raw == "ST 00015000"


@patch("terminal_drivers.keli_d2008fa.serial_session.open_serial")
def test_keli_hardware_reads_real_frame(mock_open_serial):
    ser = MagicMock()
    mock_open_serial.return_value = ser

    with patch(
        "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
        return_value=REAL_FRAME,
    ):
        result = probe_keli_hardware(KELI_CONFIG)

    assert result.success is True
    assert result.connected is True
    assert result.sample_reading is not None
    assert str(result.sample_reading.weight) == "0"
    assert result.sample_reading.stable is True
    assert result.sample_reading.unit == "kg"
    assert result.sample_reading.raw == "ST,GS,+0000000kg"
    mock_open_serial.assert_called_once()
    settings = mock_open_serial.call_args[0][0]
    assert settings.baudrate == 9600
    assert settings.parity == "none"


@patch("terminal_drivers.keli_d2008fa.serial_session.open_serial")
def test_keli_hardware_port_not_found(mock_open_serial):
    mock_open_serial.side_effect = PortProbeError(port_not_found("COM1"))
    result = probe_keli_hardware(KELI_CONFIG)
    assert result.success is False
    assert result.connected is False
    assert result.error_code == "port_not_found"


@patch("terminal_drivers.keli_d2008fa.serial_session.open_serial")
def test_keli_hardware_port_busy(mock_open_serial):
    mock_open_serial.side_effect = PortProbeError(port_access_denied("COM1", "Access is denied"))
    result = probe_keli_hardware(KELI_CONFIG)
    assert result.success is False
    assert result.error_code == "port_access_denied"


def test_keli_hardware_read_timeout():
    ser = MagicMock()
    settings = SerialSettings(port="COM1", timeout=2)
    with patch(
        "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
        return_value=b"",
    ):
        result = probe_keli_on_serial(ser, settings)
    assert result.success is False
    assert result.connected is True
    assert result.error_code == "read_timeout"


def test_keli_hardware_parse_failed():
    ser = MagicMock()
    settings = SerialSettings(port="COM1", timeout=2)
    with patch(
        "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
        return_value=b"??? no digits",
    ):
        result = probe_keli_on_serial(ser, settings)
    assert result.success is False
    assert result.connected is True
    assert result.error_code == "parse_failed"
    assert result.sample_reading is not None
    assert result.sample_reading.raw == "??? no digits"


def test_keli_test_connection_uses_hardware_not_parser_self_test():
    driver = create_terminal_driver("keli_d2008fa", KELI_CONFIG)
    with patch(
        "terminal_drivers.keli_d2008fa.driver.probe_keli_hardware",
        return_value=MagicMock(success=True, connected=True, message="ok", sample_reading=None, error_code=None),
    ) as mock_test:
        result = driver.test_connection()
    mock_test.assert_called_once_with(KELI_CONFIG)
    assert result.success is True


def test_demo_driver_unchanged():
    driver = create_terminal_driver("demo", {"target_weight": 15000})
    result = driver.test_connection()
    assert result.success is True
    assert result.connected is True
    assert "DEMO" in result.message
