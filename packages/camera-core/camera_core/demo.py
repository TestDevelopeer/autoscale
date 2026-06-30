"""DEMO camera — минимальный JPEG placeholder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hardware_core.camera import StreamStatus
from hardware_core.health import HealthReport, HealthStatus


# Минимальный валидный 1x1 JPEG
_MINIMAL_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707"
    "070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c"
    "231c1c2837292c30313434341f27393d38323c2e333432ffdb0043010909090c0b"
    "0c180d0d1832211c2132323232323232323232323232323232323232323232323232"
    "323232323232323232323232323232323232ffc0000b080001000101011100ffc4"
    "000b100001040002000000000000ffda0008010100003f00d2cfd0ffd9"
)


class DemoCameraProvider:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def get_snapshot(self) -> bytes:
        return _MINIMAL_JPEG

    def get_stream_status(self) -> StreamStatus:
        return StreamStatus.RUNNING if self._connected else StreamStatus.IDLE

    def health(self) -> HealthReport:
        return HealthReport(
            status=HealthStatus.OK if self._connected else HealthStatus.DEGRADED,
            message="DEMO camera",
            last_success_at=datetime.now(timezone.utc),
        )

    def reconnect(self) -> None:
        self.disconnect()
        self.connect()
