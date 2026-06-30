"""Низкоуровневое чтение COM-порта для probe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from terminal_drivers.probe.errors import (
    ProbeDiagnostic,
    port_access_denied,
    port_not_found,
    read_timeout,
    serial_config_mismatch,
)


@dataclass
class SerialSettings:
    port: str
    baudrate: int = 9600
    parity: str = "N"
    stop_bits: int = 1
    data_bits: int = 8
    timeout: float = 2.0
    device_id: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "parity": self.parity,
            "stop_bits": self.stop_bits,
            "data_bits": self.data_bits,
            "timeout": self.timeout,
            "device_id": self.device_id,
        }


def _parity_char(parity: str) -> str:
    mapping = {
        "n": "N",
        "none": "N",
        "e": "E",
        "even": "E",
        "o": "O",
        "odd": "O",
    }
    return mapping.get(parity.lower(), parity.upper())


def list_serial_ports() -> list[str]:
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise ImportError("pyserial не установлен: pip install pyserial") from exc
    return [p.device for p in list_ports.comports()]


def open_serial(settings: SerialSettings):
    try:
        import serial
    except ImportError as exc:
        raise ImportError("pyserial не установлен: pip install pyserial") from exc

    ports = list_serial_ports()
    if settings.port not in ports and not settings.port.startswith("/dev/"):
        # На Linux порт может быть /dev/ttyUSB0 без list match по exact name
        if not any(settings.port in p for p in ports):
            raise PortProbeError(port_not_found(settings.port))

    try:
        return serial.Serial(
            port=settings.port,
            baudrate=settings.baudrate,
            bytesize=settings.data_bits,
            parity=_parity_char(settings.parity),
            stopbits=settings.stop_bits,
            timeout=settings.timeout,
        )
    except serial.SerialException as exc:
        msg = str(exc).lower()
        if "permission" in msg or "access" in msg:
            raise PortProbeError(port_access_denied(settings.port, str(exc))) from exc
        if "could not open" in msg or "no such file" in msg:
            raise PortProbeError(port_not_found(settings.port)) from exc
        raise PortProbeError(serial_config_mismatch(str(exc))) from exc


class PortProbeError(Exception):
    def __init__(self, diagnostic: ProbeDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


def read_available(ser, max_bytes: int = 256) -> bytes:
    waiting = int(getattr(ser, "in_waiting", 0) or 0)
    if waiting <= 0:
        chunk = ser.read(max_bytes)
        return chunk or b""
    return ser.read(min(waiting, max_bytes))


def modbus_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA000
            else:
                crc >>= 1
    return crc


def build_modbus_read_holding(device_id: int, address: int = 0, count: int = 2) -> bytes:
    pdu = bytes([
        device_id & 0xFF,
        0x03,
        (address >> 8) & 0xFF,
        address & 0xFF,
        (count >> 8) & 0xFF,
        count & 0xFF,
    ])
    crc = modbus_crc16(pdu)
    return pdu + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def keli_poll_frame(settings: SerialSettings) -> bytes:
    return build_modbus_read_holding(settings.device_id)


def cas_command_wt() -> bytes:
    return b"WT\r\n"
