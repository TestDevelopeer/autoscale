"""Парсер кадров CAS CI-200A."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from hardware_core.terminal import TerminalReading


def parse_cas_frame(raw: bytes | str) -> TerminalReading:
    """
    Парсинг CAS 22-byte и текстовых кадров.

    TODO: верифицировать layout на реальном CI-200A.
    """
    if isinstance(raw, bytes):
        text = raw.decode("ascii", errors="ignore").strip()
    else:
        text = raw.strip()

    stable = "ST" in text or text.startswith("S")
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    weight = Decimal("0")
    if numbers:
        try:
            weight = Decimal(numbers[0])
        except InvalidOperation:
            weight = Decimal("0")

    return TerminalReading(
        weight=weight,
        unit="kg",
        stable=stable,
        raw=text,
        timestamp=datetime.now(timezone.utc),
        status="ok",
        protocol="cas_stream",
    )
