"""WebSocket endpoints."""

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.runtime_manager import runtime_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/health")
async def ws_health(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "health", "status": "ok"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/terminals/{terminal_id}")
async def ws_terminal(websocket: WebSocket, terminal_id: uuid.UUID) -> None:
    await websocket.accept()
    channel = f"terminal:{terminal_id}"
    queue: asyncio.Queue = asyncio.Queue()
    runtime_manager.subscribe(channel, queue)
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                reading = runtime_manager.get_terminal_reading(terminal_id)
                if reading:
                    await websocket.send_json({"type": "frame", "data": reading})
    except WebSocketDisconnect:
        runtime_manager.unsubscribe(channel, queue)


@router.websocket("/ws/workplaces/{workplace_id}")
async def ws_workplace(websocket: WebSocket, workplace_id: uuid.UUID) -> None:
    await websocket.accept()
    channel = f"workplace:{workplace_id}"
    queue: asyncio.Queue = asyncio.Queue()
    runtime_manager.subscribe(channel, queue)
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=2.0)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "workplace_id": str(workplace_id)})
    except WebSocketDisconnect:
        runtime_manager.unsubscribe(channel, queue)
