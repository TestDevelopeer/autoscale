"""Terminal endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_module
from app.models import Terminal, User
from app.services.runtime_manager import runtime_manager

router = APIRouter(prefix="/api/terminals", tags=["terminals"])


class TerminalCreate(BaseModel):
    name: str
    driver_type: str = Field(description="demo | keli_d2008fa | cas_ci200a")
    config: dict = Field(default_factory=dict)
    enabled: bool = True


class TerminalResponse(BaseModel):
    id: uuid.UUID
    name: str
    driver_type: str
    config: dict
    enabled: bool

    model_config = {"from_attributes": True}


@router.get("", dependencies=[Depends(require_module("terminals"))])
async def list_terminals(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[TerminalResponse]:
    result = await db.scalars(select(Terminal).order_by(Terminal.name))
    return [TerminalResponse.model_validate(t) for t in result.all()]


@router.post("", dependencies=[Depends(require_module("terminals"))])
async def create_terminal(
    body: TerminalCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TerminalResponse:
    terminal = Terminal(name=body.name, driver_type=body.driver_type, config=body.config, enabled=body.enabled)
    db.add(terminal)
    await db.commit()
    await db.refresh(terminal)
    return TerminalResponse.model_validate(terminal)


@router.post("/{terminal_id}/test", dependencies=[Depends(require_module("terminals"))])
async def test_terminal(terminal_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    terminal = await db.get(Terminal, terminal_id)
    if terminal is None:
        raise HTTPException(status_code=404, detail="Терминал не найден")
    return await runtime_manager.test_terminal(terminal.driver_type, terminal.config)


@router.get("/{terminal_id}/live", dependencies=[Depends(require_module("terminals"))])
async def terminal_live(terminal_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    terminal = await db.get(Terminal, terminal_id)
    if terminal is None:
        raise HTTPException(status_code=404, detail="Терминал не найден")
    await runtime_manager.start_terminal_loop(terminal.id, terminal.driver_type, terminal.config)
    reading = runtime_manager.get_terminal_reading(terminal.id)
    return {"terminal_id": str(terminal_id), "reading": reading}
