"""Парсер ответов Keli D2008FA (Modbus RTU)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from hardware_core.terminal import TerminalReading


def parse_keli_modbus_response(raw: bytes | str) -> TerminalReading:
    """
    Извлекает вес из Modbus response frame.

    TODO: уточнить register map после теста на реальном Keli D2008FA.
  """
    if isinstance(raw, bytes):
        text = raw.decode("ascii", errors="ignore")
    else:
        text = raw

    # Поиск числового фрагмента в ASCII-части ответа
    match = re.search(r"(-?\d+(?:\.\d+)?)", text)
    weight = Decimal("0")
    if match:
        try:
            weight = Decimal(match.group(1))
        except InvalidOperation:
            weight = Decimal("0")

    stable = "ST" in text.upper() or "STABLE" in text.upper() or weight > 0

    return TerminalReading(
        weight=weight,
        unit="kg",
        stable=stable,
        raw=text if isinstance(raw, str) else raw.hex(),
        timestamp=datetime.now(timezone.utc),
        status="ok",
        protocol="keli_modbus",
    )
