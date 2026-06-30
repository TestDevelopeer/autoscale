"""Интерфейс камеры."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from hardware_core.health import HealthReport


class StreamStatus(str, Enum):
    DISABLED = "disabled"
    IDLE = "idle"
    CONNECTING = "connecting"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"


class RoiRect(BaseModel):
    x: int
    y: int
    width: int
    height: int


@runtime_checkable
class CameraProvider(Protocol):
    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def get_snapshot(self) -> bytes: ...

    def get_stream_status(self) -> StreamStatus: ...

    def health(self) -> HealthReport: ...

    def reconnect(self) -> None: ...
