"""Nomeroff-net provider (opt-in)."""

from __future__ import annotations

from datetime import datetime, timezone

from hardware_core.camera import RoiRect
from alpr_core.models import PlateCandidate
from alpr_core.normalization import normalize_ru_plate


class NomeroffNetProvider:
    def __init__(self) -> None:
        from nomeroff_net import pipeline  # type: ignore[import-untyped]
        from nomeroff_net.tools import unzip  # type: ignore[import-untyped]

        self._pipeline = pipeline("number_plate_detection_and_reading", image_loader="opencv")
        self._unzip = unzip

    def recognize(self, image: bytes, roi: RoiRect | None = None) -> list[PlateCandidate]:
        # TODO: decode bytes to image array; ROI crop
        raise NotImplementedError("NomeroffNetProvider требует настройки моделей — см. docs/05-hardware-drivers.md")
