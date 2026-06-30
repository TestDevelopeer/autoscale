"""ALPR providers и нормализация номеров."""

from alpr_core.demo import DemoAlprProvider
from alpr_core.factory import create_alpr_provider
from alpr_core.models import PlateCandidate
from alpr_core.normalization import normalize_ru_plate
from alpr_core.protocol import ALPRProvider

__all__ = [
    "ALPRProvider",
    "DemoAlprProvider",
    "PlateCandidate",
    "create_alpr_provider",
    "normalize_ru_plate",
]
