"""Demo ALPR provider."""

from __future__ import annotations

from datetime import datetime, timezone

from hardware_core.camera import RoiRect
from alpr_core.models import PlateCandidate
from alpr_core.normalization import normalize_ru_plate


class DemoAlprProvider:
    def recognize(self, image: bytes, roi: RoiRect | None = None) -> list[PlateCandidate]:
        raw = "A123BC77"
        return [
            PlateCandidate(
                plate_raw=raw,
                plate_normalized=normalize_ru_plate(raw),
                confidence=0.95,
                timestamp=datetime.now(timezone.utc),
                provider="demo",
            )
        ]


class MockAlprProvider:
    def __init__(self, plates: list[tuple[str, float]] | None = None) -> None:
        self._plates = plates or [("X777XX99", 0.88)]

    def recognize(self, image: bytes, roi: RoiRect | None = None) -> list[PlateCandidate]:
        now = datetime.now(timezone.utc)
        return [
            PlateCandidate(
                plate_raw=raw,
                plate_normalized=normalize_ru_plate(raw),
                confidence=conf,
                timestamp=now,
                provider="mock",
            )
            for raw, conf in self._plates
        ]
