"""Weighing journal endpoints."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alpr_core import normalize_ru_plate
from app.database import get_db
from app.dependencies import get_current_user, require_module
from app.models import WeighingRecord, User
from app.services.weighing_service import create_weighing_from_workplace

router = APIRouter(prefix="/api/weighings", tags=["weighings"])


class WeighingResponse(BaseModel):
    id: uuid.UUID
    workplace_id: uuid.UUID
    plate_raw: str | None
    plate_normalized: str | None
    weight: Decimal | None
    unit: str
    stable: bool
    status: str
    confidence: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ConfirmWeighingBody(BaseModel):
    plate_raw: str | None = None


@router.get("", dependencies=[Depends(require_module("weighing_journal"))])
async def list_weighings(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[WeighingResponse]:
    result = await db.scalars(select(WeighingRecord).order_by(WeighingRecord.recorded_at.desc()).limit(100))
    return [WeighingResponse.model_validate(r) for r in result.all()]


@router.post("/{weighing_id}/confirm", dependencies=[Depends(require_module("weighing_journal"))])
async def confirm_weighing(
    weighing_id: uuid.UUID,
    body: ConfirmWeighingBody | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeighingResponse:
    record = await db.get(WeighingRecord, weighing_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if body and body.plate_raw:
        record.plate_raw = body.plate_raw
        record.plate_normalized = normalize_ru_plate(body.plate_raw)
    record.status = "completed"
    await db.commit()
    await db.refresh(record)
    return WeighingResponse.model_validate(record)


@router.post("/{weighing_id}/cancel", dependencies=[Depends(require_module("weighing_journal"))])
async def cancel_weighing(weighing_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> WeighingResponse:
    record = await db.get(WeighingRecord, weighing_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    record.status = "cancelled"
    await db.commit()
    await db.refresh(record)
    return WeighingResponse.model_validate(record)


__all__ = ["create_weighing_from_workplace"]
