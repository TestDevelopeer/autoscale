"""ALPR provider protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from hardware_core.camera import RoiRect
from alpr_core.models import PlateCandidate


@runtime_checkable
class ALPRProvider(Protocol):
    def recognize(self, image: bytes, roi: RoiRect | None = None) -> list[PlateCandidate]: ...
