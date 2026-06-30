"""Drivers and vehicles endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alpr_core import normalize_ru_plate
from app.database import get_db
from app.dependencies import get_current_user, require_module
from app.models import Driver, Vehicle, WeighingRecord, User

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


class DriverCreate(BaseModel):
    full_name: str
    phone: str | None = None
    organization: str | None = None
    comment: str | None = None
    plate_raw: str
    weighing_id: uuid.UUID | None = None


class DriverResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str | None
    organization: str | None
    plate_normalized: str | None = None

    model_config = {"from_attributes": True}


@router.get("", dependencies=[Depends(require_module("drivers_registry"))])
async def list_drivers(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    drivers = (await db.scalars(select(Driver).order_by(Driver.full_name))).all()
    items = []
    for d in drivers:
        vehicle = await db.scalar(select(Vehicle).where(Vehicle.driver_id == d.id))
        items.append({
            "id": str(d.id),
            "full_name": d.full_name,
            "phone": d.phone,
            "organization": d.organization,
            "plate_normalized": vehicle.plate_normalized if vehicle else None,
        })
    return items


@router.post("", dependencies=[Depends(require_module("drivers_registry"))])
async def create_driver(
    body: DriverCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    normalized = normalize_ru_plate(body.plate_raw)
    existing = await db.scalar(select(Vehicle).where(Vehicle.plate_normalized == normalized))
    if existing:
        raise HTTPException(status_code=400, detail="ТС с таким номером уже существует")

    driver = Driver(
        full_name=body.full_name,
        phone=body.phone,
        organization=body.organization,
        comment=body.comment,
    )
    db.add(driver)
    await db.flush()

    vehicle = Vehicle(plate_raw=body.plate_raw, plate_normalized=normalized, driver_id=driver.id)
    db.add(vehicle)

    if body.weighing_id:
        record = await db.get(WeighingRecord, body.weighing_id)
        if record:
            record.driver_id = driver.id
            record.vehicle_id = vehicle.id
            record.status = "completed"

    await db.commit()
    return {
        "id": str(driver.id),
        "full_name": driver.full_name,
        "plate_normalized": normalized,
    }
