"""Нормализация российских госномеров."""

from __future__ import annotations

_HOMOGLYPHS = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "У": "Y",
    "а": "A", "в": "B", "е": "E", "к": "K", "м": "M", "н": "H",
    "о": "O", "р": "P", "с": "C", "т": "T", "х": "X", "у": "Y",
})


def normalize_ru_plate(raw: str) -> str:
    text = raw.upper().translate(_HOMOGLYPHS)
    return "".join(ch for ch in text if ch.isalnum())
