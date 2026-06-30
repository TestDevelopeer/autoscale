"""Тесты runtime_manager.test_terminal для Keli (mock serial, без БД)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from app.services.runtime_manager import runtime_manager

KELI_CONFIG = {
    "port": "COM1",
    "baudrate": 9600,
    "parity": "none",
    "timeout": 2,
}

REAL_FRAME = b"ST,GS,+0000000kg"


def test_runtime_test_terminal_keli_uses_serial_layer():
    ser = MagicMock()
    with patch("terminal_drivers.keli_d2008fa.serial_session.open_serial", return_value=ser) as mock_open:
        with patch(
            "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
            return_value=REAL_FRAME,
        ):
            result = asyncio.run(runtime_manager.test_terminal("keli_d2008fa", KELI_CONFIG))

    assert result["success"] is True
    assert result["connected"] is True
    assert result["sample_reading"]["raw"] == "ST,GS,+0000000kg"
    assert str(result["sample_reading"]["weight"]) == "0"
    assert result["sample_reading"]["stable"] is True


def test_runtime_test_terminal_keli_parse_error():
    ser = MagicMock()
    with patch("terminal_drivers.keli_d2008fa.serial_session.open_serial", return_value=ser):
        with patch(
            "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
            return_value=b"??? no digits",
        ):
            result = asyncio.run(runtime_manager.test_terminal("keli_d2008fa", KELI_CONFIG))

    assert result["success"] is False
    assert result["error_code"] == "parse_failed"
    assert result["sample_reading"]["raw"] == "??? no digits"


def test_runtime_test_terminal_keli_legacy_frame_connected_true():
    ser = MagicMock()
    with patch("terminal_drivers.keli_d2008fa.serial_session.open_serial", return_value=ser):
        with patch(
            "terminal_drivers.keli_d2008fa.serial_session.read_keli_frame_once",
            return_value=b"ST 00015000",
        ):
            result = asyncio.run(runtime_manager.test_terminal("keli_d2008fa", KELI_CONFIG))

    assert result["success"] is True
    assert result["connected"] is True
    assert result["sample_reading"]["raw"] == "ST 00015000"
    assert str(result["sample_reading"]["weight"]) == "15000"
    assert result["sample_reading"]["stable"] is True


def test_runtime_test_terminal_demo_connected_true():
    result = asyncio.run(runtime_manager.test_terminal("demo", {"target_weight": 15000}))
    assert result["success"] is True
    assert result["connected"] is True
    assert "DEMO" in result["message"]
