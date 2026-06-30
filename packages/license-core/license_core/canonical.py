"""Каноническая сериализация payload для подписи лицензии."""

from __future__ import annotations

import json
from typing import Any


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    """Единый формат для Python и PHP: sort_keys + compact separators."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
