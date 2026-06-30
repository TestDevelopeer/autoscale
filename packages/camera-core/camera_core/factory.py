"""Фабрика camera providers."""

from __future__ import annotations

from typing import Any

from camera_core.demo import DemoCameraProvider
from camera_core.http_snapshot import HttpSnapshotProvider

PROVIDER_TYPES = {
    "demo": DemoCameraProvider,
    "http": HttpSnapshotProvider,
    "http_snapshot": HttpSnapshotProvider,
}


def create_camera_provider(connection_type: str, config: dict[str, Any]):
    cls = PROVIDER_TYPES.get(connection_type)
    if cls is None:
        raise ValueError(f"Unknown camera connection type: {connection_type}")
    return cls(config)
