"""State machine взвешивания."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from alpr_core.models import PlateCandidate
from hardware_core.terminal import TerminalReading


class WeighingState(str, Enum):
    IDLE = "IDLE"
    VEHICLE_DETECTED = "VEHICLE_DETECTED"
    PLATE_DETECTING = "PLATE_DETECTING"
    PLATE_CANDIDATE_FOUND = "PLATE_CANDIDATE_FOUND"
    WEIGHT_WAITING = "WEIGHT_WAITING"
    WEIGHT_STABILIZING = "WEIGHT_STABILIZING"
    READY_TO_CAPTURE = "READY_TO_CAPTURE"
    CAPTURED = "CAPTURED"
    DRIVER_LOOKUP = "DRIVER_LOOKUP"
    NEED_DRIVER_CREATE = "NEED_DRIVER_CREATE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


@dataclass
class WorkplaceConfig:
    min_weight_threshold: Decimal = Decimal("100")
    stable_seconds: float = 2.0
    max_weight_delta: Decimal = Decimal("5")
    auto_confirm: bool = True
    alpr_enabled: bool = True
    min_plate_confidence: float = 0.7


@dataclass
class WeighingContext:
    workplace_id: str
    state: WeighingState = WeighingState.IDLE
    weight_readings: list[TerminalReading] = field(default_factory=list)
    plate_candidates: list[PlateCandidate] = field(default_factory=list)
    best_plate: PlateCandidate | None = None
    terminal_raw: str | None = None
    stable_since: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WorkplaceOrchestrator:
    """Явная FSM взвешивания — тестируется отдельно от hardware."""

    def __init__(self, config: WorkplaceConfig) -> None:
        self._config = config
        self._ctx = WeighingContext(workplace_id="")

    @property
    def context(self) -> WeighingContext:
        return self._ctx

    def reset(self, workplace_id: str) -> None:
        self._ctx = WeighingContext(workplace_id=workplace_id, state=WeighingState.IDLE)

    def on_weight(self, reading: TerminalReading) -> WeighingState:
        self._ctx.weight_readings.append(reading)
        if len(self._ctx.weight_readings) > 50:
            self._ctx.weight_readings = self._ctx.weight_readings[-50:]
        self._ctx.terminal_raw = reading.raw
        self._ctx.updated_at = datetime.now(timezone.utc)

        weight = reading.weight
        threshold = self._config.min_weight_threshold

        if self._ctx.state == WeighingState.IDLE and weight >= threshold:
            self._ctx.state = WeighingState.VEHICLE_DETECTED
        elif self._ctx.state == WeighingState.VEHICLE_DETECTED:
            self._ctx.state = WeighingState.PLATE_DETECTING if self._config.alpr_enabled else WeighingState.WEIGHT_WAITING
        elif self._ctx.state in (WeighingState.PLATE_DETECTING, WeighingState.PLATE_CANDIDATE_FOUND):
            if weight < threshold:
                self._ctx.state = WeighingState.IDLE
            elif self._ctx.best_plate and self._ctx.state == WeighingState.PLATE_DETECTING:
                self._ctx.state = WeighingState.PLATE_CANDIDATE_FOUND
            if self._ctx.state == WeighingState.PLATE_CANDIDATE_FOUND:
                self._ctx.state = WeighingState.WEIGHT_WAITING
        elif self._ctx.state in (WeighingState.WEIGHT_WAITING, WeighingState.WEIGHT_STABILIZING, WeighingState.READY_TO_CAPTURE):
            if weight < threshold:
                self._ctx.state = WeighingState.IDLE
                self._ctx.stable_since = None
            elif self._is_stable(reading):
                if self._ctx.stable_since is None:
                    self._ctx.stable_since = datetime.now(timezone.utc)
                    self._ctx.state = WeighingState.WEIGHT_STABILIZING
                elif (datetime.now(timezone.utc) - self._ctx.stable_since).total_seconds() >= self._config.stable_seconds:
                    if self._can_capture():
                        self._ctx.state = WeighingState.READY_TO_CAPTURE
            else:
                self._ctx.stable_since = None
                self._ctx.state = WeighingState.WEIGHT_WAITING

        return self._ctx.state

    def on_plate_candidates(self, candidates: list[PlateCandidate]) -> None:
        self._ctx.plate_candidates.extend(candidates)
        if len(self._ctx.plate_candidates) > 20:
            self._ctx.plate_candidates = self._ctx.plate_candidates[-20:]
        best = max(candidates, key=lambda c: c.confidence, default=None)
        if best and best.confidence >= self._config.min_plate_confidence:
            self._ctx.best_plate = best
            if self._ctx.state == WeighingState.PLATE_DETECTING:
                self._ctx.state = WeighingState.PLATE_CANDIDATE_FOUND

    def capture(self) -> WeighingState:
        if self._ctx.state != WeighingState.READY_TO_CAPTURE:
            raise ValueError(f"Cannot capture in state {self._ctx.state}")
        self._ctx.state = WeighingState.CAPTURED
        return self._ctx.state

    def after_driver_lookup(self, found: bool) -> WeighingState:
        if self._ctx.state != WeighingState.CAPTURED:
            return self._ctx.state
        self._ctx.state = WeighingState.DRIVER_LOOKUP
        self._ctx.state = WeighingState.COMPLETED if found else WeighingState.NEED_DRIVER_CREATE
        return self._ctx.state

    def complete(self) -> WeighingState:
        self._ctx.state = WeighingState.COMPLETED
        return self._ctx.state

    def cancel(self) -> WeighingState:
        self._ctx.state = WeighingState.CANCELLED
        return self._ctx.state

    def _is_stable(self, reading: TerminalReading) -> bool:
        if reading.stable:
            return True
        if len(self._ctx.weight_readings) < 2:
            return False
        recent = self._ctx.weight_readings[-5:]
        weights = [r.weight for r in recent]
        delta = max(weights) - min(weights)
        return delta <= self._config.max_weight_delta

    def _can_capture(self) -> bool:
        if self._config.alpr_enabled and self._ctx.best_plate is None:
            return False
        if self._ctx.weight_readings and self._ctx.weight_readings[-1].weight < self._config.min_weight_threshold:
            return False
        return True
