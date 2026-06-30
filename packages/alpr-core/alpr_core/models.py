"""Модели ALPR."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlateCandidate(BaseModel):
    plate_raw: str
    plate_normalized: str
    confidence: float
    region: dict[str, int] | None = None
    timestamp: datetime | None = None
    provider: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
