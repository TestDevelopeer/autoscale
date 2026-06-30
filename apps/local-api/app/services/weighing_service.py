"""Создание записей журнала из FSM."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Vehicle, WeighingRecord, Workplace
from app.services.runtime_manager import runtime_manager
from app.services.workplace_orchestrator import WorkplaceConfig


async def create_weighing_from_workplace(
    db: AsyncSession,
    workplace: Workplace,
    operator_id: uuid.UUID,
) -> WeighingRecord | None:
    """Создание записи из orchestrator context после capture."""
    config = WorkplaceConfig(
        min_weight_threshold=workplace.min_weight_threshold,
        stable_seconds=float(workplace.stable_seconds),
        max_weight_delta=workplace.max_weight_delta,
        auto_confirm=workplace.auto_confirm,
        alpr_enabled=workplace.alpr_provider != "disabled",
    )
    orch = runtime_manager.get_orchestrator(workplace.id, config)
    reading = runtime_manager.get_terminal_reading(workplace.terminal_id) or {}
    plate = orch.context.best_plate

    if plate and plate.plate_normalized and workplace.duplicate_protection_window_sec > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=workplace.duplicate_protection_window_sec)
        duplicate = await db.scalar(
            select(WeighingRecord).where(
                WeighingRecord.workplace_id == workplace.id,
                WeighingRecord.plate_normalized == plate.plate_normalized,
                WeighingRecord.recorded_at >= cutoff,
                WeighingRecord.status != "cancelled",
            )
        )
        if duplicate is not None:
            return duplicate

    record = WeighingRecord(
        workplace_id=workplace.id,
        terminal_id=workplace.terminal_id,
        operator_id=operator_id,
        plate_raw=plate.plate_raw if plate else None,
        plate_normalized=plate.plate_normalized if plate else None,
        weight=reading.get("weight"),
        unit=reading.get("unit", "kg"),
        stable=bool(reading.get("stable")),
        confidence=plate.confidence if plate else None,
        status="draft",
        fsm_state=orch.context.state.value,
        terminal_raw=reading.get("raw"),
        plate_alternatives=[c.model_dump(mode="json") for c in orch.context.plate_candidates[-5:]],
    )

    found = False
    if plate and plate.plate_normalized:
        vehicle = await db.scalar(select(Vehicle).where(Vehicle.plate_normalized == plate.plate_normalized))
        if vehicle:
            record.vehicle_id = vehicle.id
            record.driver_id = vehicle.driver_id
            record.status = "completed"
            found = True
        else:
            record.status = "need_driver_create"

    db.add(record)
    orch.after_driver_lookup(found=found)
    workplace.fsm_state = orch.context.state.value
    await db.commit()
    await db.refresh(record)
    return record
