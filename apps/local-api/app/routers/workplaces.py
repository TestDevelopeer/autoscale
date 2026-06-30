"""Workplace endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_module
from app.models import Camera, Terminal, Workplace, WorkplaceCamera, User
from app.services.runtime_manager import runtime_manager
from app.services.workplace_orchestrator import WorkplaceConfig

router = APIRouter(prefix="/api/workplaces", tags=["workplaces"])


class WorkplaceCreate(BaseModel):
    name: str
    terminal_id: uuid.UUID
    camera_ids: list[uuid.UUID] = Field(default_factory=list)
    alpr_provider: str = "demo"
    min_weight_threshold: Decimal = Decimal("100")
    stable_seconds: float = 2.0
    max_weight_delta: Decimal = Decimal("5")
    auto_confirm: bool = True
    manual_confirm: bool = False
    snapshot_policy: str = "on_capture"
    duplicate_protection_window_sec: int = 60
    enabled: bool = True


class WorkplaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    terminal_id: uuid.UUID
    alpr_provider: str
    enabled: bool
    is_running: bool
    fsm_state: str

    model_config = {"from_attributes": True}


@router.get("", dependencies=[Depends(require_module("workplaces"))])
async def list_workplaces(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[WorkplaceResponse]:
    result = await db.scalars(select(Workplace).order_by(Workplace.name))
    return [WorkplaceResponse.model_validate(w) for w in result.all()]


@router.post("", dependencies=[Depends(require_module("workplaces"))])
async def create_workplace(
    body: WorkplaceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WorkplaceResponse:
    if await db.get(Terminal, body.terminal_id) is None:
        raise HTTPException(status_code=400, detail="Терминал не найден")

    workplace = Workplace(
        name=body.name,
        terminal_id=body.terminal_id,
        alpr_provider=body.alpr_provider,
        min_weight_threshold=body.min_weight_threshold,
        stable_seconds=body.stable_seconds,
        max_weight_delta=body.max_weight_delta,
        auto_confirm=body.auto_confirm,
        manual_confirm=body.manual_confirm,
        snapshot_policy=body.snapshot_policy,
        duplicate_protection_window_sec=body.duplicate_protection_window_sec,
        enabled=body.enabled,
    )
    db.add(workplace)
    await db.flush()

    for camera_id in body.camera_ids:
        if await db.get(Camera, camera_id) is None:
            raise HTTPException(status_code=400, detail=f"Камера {camera_id} не найдена")
        db.add(WorkplaceCamera(workplace_id=workplace.id, camera_id=camera_id))

    await db.commit()
    await db.refresh(workplace)
    return WorkplaceResponse.model_validate(workplace)


@router.post("/{workplace_id}/start", dependencies=[Depends(require_module("workplaces"))])
async def start_workplace(workplace_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    workplace = await db.scalar(
        select(Workplace).where(Workplace.id == workplace_id).options(selectinload(Workplace.cameras))
    )
    if workplace is None:
        raise HTTPException(status_code=404, detail="Рабочее место не найдено")

    terminal = await db.get(Terminal, workplace.terminal_id)
    if terminal is None:
        raise HTTPException(status_code=400, detail="Терминал не привязан")

    await runtime_manager.start_terminal_loop(terminal.id, terminal.driver_type, terminal.config)

    config = WorkplaceConfig(
        min_weight_threshold=workplace.min_weight_threshold,
        stable_seconds=float(workplace.stable_seconds),
        max_weight_delta=workplace.max_weight_delta,
        auto_confirm=workplace.auto_confirm,
        alpr_enabled=workplace.alpr_provider != "disabled",
    )
    orch = runtime_manager.get_orchestrator(workplace.id, config)
    orch.reset(str(workplace.id))

    await runtime_manager.start_workplace_loop(
        workplace.id,
        terminal.id,
        config,
        workplace.alpr_provider,
        user.id,
    )

    workplace.is_running = True
    workplace.fsm_state = "VEHICLE_DETECTED"
    await db.commit()

    return {"workplace_id": str(workplace_id), "state": workplace.fsm_state, "message": "started"}


@router.post("/{workplace_id}/stop", dependencies=[Depends(require_module("workplaces"))])
async def stop_workplace(workplace_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    workplace = await db.get(Workplace, workplace_id)
    if workplace is None:
        raise HTTPException(status_code=404, detail="Рабочее место не найдено")
    workplace.is_running = False
    workplace.fsm_state = "IDLE"
    await runtime_manager.stop_workplace_loop(workplace_id)
    await runtime_manager.stop_terminal_loop(workplace.terminal_id)
    await db.commit()
    return {"workplace_id": str(workplace_id), "state": "IDLE"}
