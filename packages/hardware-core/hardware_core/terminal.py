"""Интерфейс весового терминала."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from hardware_core.health import HealthReport


class TerminalReading(BaseModel):
    weight: Decimal = Decimal("0")
    unit: str = "kg"
    stable: bool = False
    raw: str = ""
    timestamp: datetime | None = None
    status: str = "ok"
    error: str | None = None
    protocol: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class TerminalStatus(BaseModel):
    connected: bool = False
    protocol: str = ""
    last_reading: TerminalReading | None = None


class TerminalCapabilities(BaseModel):
    supports_zero: bool = False
    supports_stream: bool = True
    supports_command_mode: bool = False
    protocols: list[str] = Field(default_factory=list)


class TestResult(BaseModel):
    success: bool
    message: str = ""
    sample_reading: TerminalReading | None = None


@runtime_checkable
class TerminalDriver(Protocol):
    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def test_connection(self) -> TestResult: ...

    def read_frame(self) -> bytes | str: ...

    def parse_frame(self, raw: bytes | str) -> TerminalReading: ...

    def get_current_weight(self) -> TerminalReading: ...

    def get_status(self) -> TerminalStatus: ...

    def zero(self) -> bool: ...

    def health(self) -> HealthReport: ...

    def capabilities(self) -> TerminalCapabilities: ...
