"""Реальное чтение COM для Keli D2008FA (переиспользует probe.serial_io)."""

from __future__ import annotations

import time
from typing import Any

from hardware_core.terminal import TerminalReading, TestResult
from terminal_drivers.keli_d2008fa.parser import parse_keli_modbus_response
from terminal_drivers.probe.errors import ProbeErrorCode
from terminal_drivers.probe.serial_io import (
    PortProbeError,
    SerialSettings,
    keli_poll_frame,
    open_serial,
    read_available,
)


def serial_settings_from_config(config: dict[str, Any]) -> SerialSettings:
    """Собирает настройки COM из config терминала."""
    return SerialSettings(
        port=str(config["port"]),
        baudrate=int(config.get("baudrate", 9600)),
        parity=str(config.get("parity", "none")),
        stop_bits=int(config.get("stop_bits", 1)),
        data_bits=int(config.get("data_bits", 8)),
        timeout=float(config.get("timeout", 2.0)),
        device_id=int(config.get("device_id", 1)),
    )


def read_keli_frame_once(ser, settings: SerialSettings) -> bytes:
    """Одно чтение кадра Keli: stream в буфере или Modbus poll."""
    chunk = read_available(ser)
    if chunk:
        return chunk
    ser.write(keli_poll_frame(settings))
    ser.flush()
    time.sleep(0.05)
    return read_available(ser)


def _probe_error_result(exc: PortProbeError) -> TestResult:
    return TestResult(
        success=False,
        connected=False,
        message=exc.diagnostic.message,
        error_code=exc.diagnostic.code.value,
    )


def _evaluate_raw(raw_bytes: bytes, settings: SerialSettings) -> TestResult:
    if not raw_bytes:
        return TestResult(
            success=False,
            connected=True,
            message=f"Timeout чтения с {settings.port} ({settings.timeout}s)",
            error_code=ProbeErrorCode.READ_TIMEOUT.value,
        )

    reading = parse_keli_modbus_response(raw_bytes)
    if reading.status != "ok" or reading.error:
        return TestResult(
            success=False,
            connected=True,
            message=reading.error or "Получен raw frame, но parser не смог извлечь вес",
            error_code=ProbeErrorCode.PARSE_FAILED.value,
            sample_reading=reading,
        )

    return TestResult(
        success=True,
        connected=True,
        message="Keli D2008FA: подключение успешно",
        sample_reading=reading,
    )


def probe_keli_on_serial(ser, settings: SerialSettings) -> TestResult:
    """Проверка на уже открытом COM-порте."""
    try:
        raw = read_keli_frame_once(ser, settings)
        return _evaluate_raw(raw, settings)
    except PortProbeError as exc:
        return _probe_error_result(exc)


def probe_keli_hardware(config: dict[str, Any]) -> TestResult:
    """Открывает COM, читает кадр Keli и возвращает результат проверки."""
    port = config.get("port")
    if not port:
        return TestResult(
            success=False,
            connected=False,
            message="Для Keli D2008FA укажите COM-порт",
            error_code="port_required",
        )

    settings = serial_settings_from_config(config)
    try:
        ser = open_serial(settings)
    except ImportError as exc:
        return TestResult(
            success=False,
            connected=False,
            message=str(exc),
            error_code=ProbeErrorCode.SERIAL_UNAVAILABLE.value,
        )
    except PortProbeError as exc:
        return _probe_error_result(exc)

    try:
        return probe_keli_on_serial(ser, settings)
    finally:
        try:
            ser.close()
        except Exception:
            pass


def read_keli_reading(config: dict[str, Any], ser) -> TerminalReading | None:
    """Читает и парсит один кадр на открытом порте."""
    settings = serial_settings_from_config(config)
    raw = read_keli_frame_once(ser, settings)
    if not raw:
        return None
    reading = parse_keli_modbus_response(raw)
    if reading.status == "ok" and not reading.error:
        return reading
    return reading
