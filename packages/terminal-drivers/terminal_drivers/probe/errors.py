"""Диагностика ошибок hardware probe."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProbeErrorCode(str, Enum):
    PORT_NOT_FOUND = "port_not_found"
    PORT_ACCESS_DENIED = "port_access_denied"
    READ_TIMEOUT = "read_timeout"
    TERMINAL_SILENT = "terminal_silent"
    PARSE_FAILED = "parse_failed"
    SERIAL_CONFIG = "serial_config"
    UNSTABLE_WEIGHT = "unstable_weight"
    NO_STABLE_FLAG = "no_stable_flag"
    DRIVER_UNKNOWN = "driver_unknown"
    SERIAL_UNAVAILABLE = "serial_unavailable"


@dataclass(frozen=True)
class ProbeDiagnostic:
    code: ProbeErrorCode
    message: str
    hint: str = ""

    def to_dict(self) -> dict:
        return {"code": self.code.value, "message": self.message, "hint": self.hint}


def port_not_found(port: str) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.PORT_NOT_FOUND,
        message=f"COM-порт не найден: {port}",
        hint="Проверьте кабель, диспетчер устройств и имя порта (например COM3, /dev/ttyUSB0).",
    )


def port_access_denied(port: str, detail: str = "") -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.PORT_ACCESS_DENIED,
        message=f"Нет доступа к порту {port}" + (f": {detail}" if detail else ""),
        hint="Закройте другие программы, использующие порт; проверьте права пользователя.",
    )


def read_timeout(port: str, seconds: float) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.READ_TIMEOUT,
        message=f"Timeout чтения с {port} ({seconds}s)",
        hint="Проверьте baudrate, parity, подключение TX/RX и питание терминала.",
    )


def terminal_silent(port: str, duration: float) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.TERMINAL_SILENT,
        message=f"Терминал молчит на {port} за {duration}s",
        hint="Проверьте кабель, режим терминала (stream/Modbus) и настройки порта.",
    )


def parse_failed(raw_preview: str) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.PARSE_FAILED,
        message="Получен raw frame, но parser не смог извлечь вес",
        hint=f"Сохраните raw sample для анализа. Превью: {raw_preview[:120]}",
    )


def serial_config_mismatch(detail: str) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.SERIAL_CONFIG,
        message=f"Возможно неверные настройки порта: {detail}",
        hint="Сверьте baudrate/parity/stop bits с паспортом терминала.",
    )


def unstable_weight(weight: str) -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.UNSTABLE_WEIGHT,
        message=f"Вес прочитан ({weight}), но флаг stable=false",
        hint="Дождитесь стабилизации на весах или проверьте парсер stable-флага.",
    )


def no_stable_flag() -> ProbeDiagnostic:
    return ProbeDiagnostic(
        code=ProbeErrorCode.NO_STABLE_FLAG,
        message="Вес прочитан, но stable-флаг не обнаружен в кадре",
        hint="Проверьте формат кадра (ST/STABLE) на реальном терминале.",
    )
