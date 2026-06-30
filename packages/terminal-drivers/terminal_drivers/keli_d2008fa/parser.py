"""Парсер ответов Keli D2008FA (ASCII continuous и legacy polling)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from hardware_core.terminal import TerminalReading

# ST,GS,+0000000kg — непрерывный ASCII-формат Keli D2008FA
ASCII_CONTINUOUS_RE = re.compile(
    r"^\s*(?P<stability>ST|US)\s*,\s*(?P<weight_type>GS|NT)\s*,\s*"
    r"(?P<sign>[+-])\s*(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>kg|g|t|lb)?\s*$",
    re.IGNORECASE,
)

# Legacy: "ST 00015000" / "US 00015000"
LEGACY_SPACE_RE = re.compile(
    r"^\s*(?P<stability>ST|US)\s+(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>kg|g|t|lb)?\s*$",
    re.IGNORECASE,
)

FALLBACK_NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def _normalize_text(raw: bytes | str) -> str:
    if isinstance(raw, bytes):
        text = raw.decode("ascii", errors="ignore")
    else:
        text = raw
    return text.strip("\r\n \t")


def _raw_repr(raw: bytes | str, text: str) -> str:
    if isinstance(raw, str):
        return text
    return text


def _weight_type_label(code: str) -> str:
    mapping = {"GS": "gross", "NT": "net"}
    return mapping.get(code.upper(), code.lower())


def _apply_sign(sign: str, value: str) -> Decimal:
    weight = Decimal(value)
    if sign == "-":
        weight = -weight
    return weight


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal("0")


def _parse_error(text: str, raw: bytes | str) -> TerminalReading:
    return TerminalReading(
        weight=Decimal("0"),
        unit="kg",
        stable=False,
        raw=_raw_repr(raw, text),
        timestamp=datetime.now(timezone.utc),
        status="parse_error",
        error="Не удалось извлечь вес из кадра Keli",
        protocol="keli_modbus",
    )


def _ok_reading(
    *,
    text: str,
    raw: bytes | str,
    weight: Decimal,
    unit: str,
    stable: bool,
    metadata: dict | None = None,
) -> TerminalReading:
    return TerminalReading(
        weight=weight,
        unit=unit,
        stable=stable,
        raw=_raw_repr(raw, text),
        timestamp=datetime.now(timezone.utc),
        status="ok",
        protocol="keli_modbus",
        metadata=metadata or {},
    )


def parse_keli_modbus_response(raw: bytes | str) -> TerminalReading:
    """
    Извлекает вес из кадра Keli D2008FA.

    Поддерживаемые форматы:
    - ASCII continuous: ST,GS,+0000000kg
    - Legacy polling: ST 00015000
    - Встроенный ASCII в бинарном Modbus-ответе (fallback)
    """
    text = _normalize_text(raw)

    match = ASCII_CONTINUOUS_RE.match(text)
    if match:
        stable = match.group("stability").upper() == "ST"
        weight = _apply_sign(match.group("sign"), match.group("value"))
        unit = (match.group("unit") or "kg").lower()
        return _ok_reading(
            text=text,
            raw=raw,
            weight=weight,
            unit=unit,
            stable=stable,
            metadata={"weight_type": _weight_type_label(match.group("weight_type"))},
        )

    match = LEGACY_SPACE_RE.match(text)
    if match:
        stable = match.group("stability").upper() == "ST"
        weight = _parse_decimal(match.group("value"))
        unit = (match.group("unit") or "kg").lower()
        return _ok_reading(
            text=text,
            raw=raw,
            weight=weight,
            unit=unit,
            stable=stable,
        )

    number_match = FALLBACK_NUMBER_RE.search(text)
    if not number_match:
        return _parse_error(text, raw)

    stable = "ST" in text.upper() or "STABLE" in text.upper()
    return _ok_reading(
        text=text,
        raw=raw,
        weight=_parse_decimal(number_match.group(1)),
        unit="kg",
        stable=stable,
    )
