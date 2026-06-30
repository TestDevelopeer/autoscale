"""Camera endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_module
from app.models import Camera, User
from app.services.runtime_manager import runtime_manager

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


class CameraCreate(BaseModel):
    name: str
    connection_type: str = Field(description="demo | http | rtsp")
    config: dict = Field(default_factory=dict)
    alpr_provider: str = "demo"
    roi: dict | None = None
    enabled: bool = True


class CameraResponse(BaseModel):
    id: uuid.UUID
    name: str
    connection_type: str
    config: dict
    alpr_provider: str
    roi: dict | None
    enabled: bool

    model_config = {"from_attributes": True}


@router.get("", dependencies=[Depends(require_module("cameras"))])
async def list_cameras(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[CameraResponse]:
    result = await db.scalars(select(Camera).order_by(Camera.name))
    return [CameraResponse.model_validate(c) for c in result.all()]


@router.post("", dependencies=[Depends(require_module("cameras"))])
async def create_camera(
    body: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CameraResponse:
    camera = Camera(
        name=body.name,
        connection_type=body.connection_type,
        config=body.config,
        alpr_provider=body.alpr_provider,
        roi=body.roi,
        enabled=body.enabled,
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return CameraResponse.model_validate(camera)


@router.post("/alpr/test", dependencies=[Depends(require_module("alpr"))])
async def test_alpr(provider: str = "demo", user: User = Depends(get_current_user)) -> dict:
    return await runtime_manager.test_alpr(provider)


@router.post("/{camera_id}/test", dependencies=[Depends(require_module("cameras"))])
async def test_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Камера не найдена")
    return await runtime_manager.test_camera(camera.connection_type, camera.config)
