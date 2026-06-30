"""DEMO terminal driver — синтетический вес для разработки."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from hardware_core.health import HealthReport, HealthStatus
from hardware_core.terminal import (
    TerminalCapabilities,
    TerminalReading,
    TerminalStatus,
    TestResult,
)


class DemoTerminalDriver:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self._target_weight = Decimal(str(config.get("target_weight", 15000)))
        self._ramp_seconds = float(config.get("ramp_seconds", 3.0))
        self._stable_after = float(config.get("stable_after", 4.0))
        self._departure_seconds = float(config.get("departure_seconds", 2.0))
        self._connected = False
        self._started_at: float | None = None
        self._departure_started_at: float | None = None

    def connect(self) -> None:
        self._connected = True
        self._started_at = time.monotonic()

    def disconnect(self) -> None:
        self._connected = False
        self._started_at = None
        self._departure_started_at = None

    def signal_departure(self) -> None:
        """Симуляция съезда с весов после взвешивания (demo)."""
        self._departure_started_at = time.monotonic()

    def _elapsed(self) -> float:
        if self._started_at is None:
            return 0.0
        return time.monotonic() - self._started_at

    def _synthetic_reading(self) -> TerminalReading:
        if self._departure_started_at is not None:
            elapsed = time.monotonic() - self._departure_started_at
            if elapsed < self._departure_seconds:
                factor = max(0.0, 1.0 - elapsed / self._departure_seconds)
                weight = (self._target_weight * Decimal(str(factor))).quantize(Decimal("0.01"))
            else:
                weight = Decimal("0")
            stable = weight == Decimal("0")
            return TerminalReading(
                weight=weight,
                unit="kg",
                stable=stable,
                raw=f"DEMO departure weight={weight} stable={stable}",
                timestamp=datetime.now(timezone.utc),
                status="ok",
                protocol="demo",
            )

        elapsed = self._elapsed()
        if elapsed < self._ramp_seconds:
            weight = self._target_weight * Decimal(str(elapsed / self._ramp_seconds))
            stable = False
        else:
            weight = self._target_weight
            stable = elapsed >= self._stable_after

        return TerminalReading(
            weight=weight.quantize(Decimal("0.01")),
            unit="kg",
            stable=stable,
            raw=f"DEMO weight={weight} stable={stable}",
            timestamp=datetime.now(timezone.utc),
            status="ok",
            protocol="demo",
        )

    def test_connection(self) -> TestResult:
        reading = self._synthetic_reading()
        return TestResult(
            success=True,
            connected=True,
            message="DEMO terminal OK",
            sample_reading=reading,
        )

    def read_frame(self) -> str:
        return self._synthetic_reading().raw

    def parse_frame(self, raw: bytes | str) -> TerminalReading:
        return self._synthetic_reading()

    def get_current_weight(self) -> TerminalReading:
        return self._synthetic_reading()

    def get_status(self) -> TerminalStatus:
        reading = self._synthetic_reading()
        return TerminalStatus(connected=self._connected, protocol="demo", last_reading=reading)

    def zero(self) -> bool:
        self._started_at = time.monotonic()
        self._departure_started_at = None
        return True

    def health(self) -> HealthReport:
        return HealthReport(
            status=HealthStatus.OK if self._connected else HealthStatus.DEGRADED,
            message="DEMO terminal",
            last_success_at=datetime.now(timezone.utc),
        )

    def capabilities(self) -> TerminalCapabilities:
        return TerminalCapabilities(
            supports_zero=True,
            supports_stream=True,
            protocols=["demo"],
        )
