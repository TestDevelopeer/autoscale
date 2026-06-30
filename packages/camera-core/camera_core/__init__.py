"""Провайдеры камер."""

from camera_core.demo import DemoCameraProvider
from camera_core.factory import create_camera_provider
from camera_core.http_snapshot import HttpSnapshotProvider

__all__ = ["DemoCameraProvider", "HttpSnapshotProvider", "create_camera_provider"]
