"""Общие интерфейсы оборудования."""

from hardware_core.camera import CameraProvider, StreamStatus
from hardware_core.health import HealthReport, HealthStatus
from hardware_core.terminal import (
    TerminalCapabilities,
    TerminalDriver,
    TerminalReading,
    TerminalStatus,
    TestResult,
)

__all__ = [
    "CameraProvider",
    "StreamStatus",
    "HealthReport",
    "HealthStatus",
    "TerminalCapabilities",
    "TerminalDriver",
    "TerminalReading",
    "TerminalStatus",
    "TestResult",
]
