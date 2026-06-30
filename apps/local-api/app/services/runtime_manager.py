"""Runtime менеджер терминалов и камер."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from terminal_drivers import create_terminal_driver
from camera_core import create_camera_provider
from alpr_core import create_alpr_provider
from hardware_core.terminal import TestResult, normalize_test_result

from app.services.workplace_orchestrator import WorkplaceConfig, WorkplaceOrchestrator, WeighingState


class RuntimeManager:
    def __init__(self) -> None:
        self._terminal_tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._terminal_readings: dict[uuid.UUID, dict] = {}
        self._terminal_drivers: dict[uuid.UUID, Any] = {}
        self._workplace_tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._workplace_meta: dict[uuid.UUID, dict[str, Any]] = {}
        self._orchestrators: dict[uuid.UUID, WorkplaceOrchestrator] = {}
        self._subscribers: dict[str, list[Any]] = {}

    def get_terminal_reading(self, terminal_id: uuid.UUID) -> dict | None:
        return self._terminal_readings.get(terminal_id)

    async def start_terminal_loop(self, terminal_id: uuid.UUID, driver_type: str, config: dict) -> None:
        if terminal_id in self._terminal_tasks:
            return

        driver = create_terminal_driver(driver_type, config)
        driver.connect()
        self._terminal_drivers[terminal_id] = driver

        async def _loop() -> None:
            while terminal_id in self._terminal_tasks:
                reading = driver.get_current_weight()
                data = reading.model_dump(mode="json")
                self._terminal_readings[terminal_id] = data
                await self._broadcast(f"terminal:{terminal_id}", {"type": "frame", "data": data})
                await asyncio.sleep(0.2)

        self._terminal_tasks[terminal_id] = asyncio.create_task(_loop())

    async def stop_terminal_loop(self, terminal_id: uuid.UUID) -> None:
        task = self._terminal_tasks.pop(terminal_id, None)
        self._terminal_drivers.pop(terminal_id, None)
        if task:
            task.cancel()

    def get_orchestrator(self, workplace_id: uuid.UUID, config: WorkplaceConfig) -> WorkplaceOrchestrator:
        if workplace_id not in self._orchestrators:
            orch = WorkplaceOrchestrator(config)
            orch.reset(str(workplace_id))
            self._orchestrators[workplace_id] = orch
        return self._orchestrators[workplace_id]

    async def tick_workplace(
        self,
        workplace_id: uuid.UUID,
        terminal_id: uuid.UUID,
        config: WorkplaceConfig,
        alpr_provider: str = "demo",
    ) -> dict:
        """Один тик FSM: вес, ALPR, auto-capture."""
        from hardware_core.terminal import TerminalReading
        from camera_core.demo import DemoCameraProvider

        orch = self.get_orchestrator(workplace_id, config)
        reading_data = self._terminal_readings.get(terminal_id)

        if reading_data:
            reading = TerminalReading.model_validate(reading_data)
            orch.on_weight(reading)

            if config.alpr_enabled and alpr_provider != "disabled":
                if orch.context.state in (
                    WeighingState.PLATE_DETECTING,
                    WeighingState.PLATE_CANDIDATE_FOUND,
                    WeighingState.WEIGHT_WAITING,
                ):
                    provider = create_alpr_provider(alpr_provider)
                    image = DemoCameraProvider().get_snapshot()
                    candidates = provider.recognize(image)
                    if candidates:
                        orch.on_plate_candidates(candidates)

            meta = self._workplace_meta.get(workplace_id, {})
            if (
                config.auto_confirm
                and orch.context.state == WeighingState.READY_TO_CAPTURE
                and not meta.get("captured")
            ):
                try:
                    orch.capture()
                    meta["captured"] = True
                    meta["needs_journal"] = True
                except ValueError:
                    pass

        payload = {
            "type": "state_changed",
            "state": orch.context.state.value,
            "weight": reading_data,
            "plate_candidate": orch.context.best_plate.model_dump(mode="json") if orch.context.best_plate else None,
        }
        await self._broadcast(f"workplace:{workplace_id}", payload)
        return payload

    async def start_workplace_loop(
        self,
        workplace_id: uuid.UUID,
        terminal_id: uuid.UUID,
        config: WorkplaceConfig,
        alpr_provider: str,
        operator_id: uuid.UUID,
    ) -> None:
        if workplace_id in self._workplace_tasks:
            return

        self._workplace_meta[workplace_id] = {
            "terminal_id": terminal_id,
            "config": config,
            "alpr_provider": alpr_provider,
            "operator_id": operator_id,
            "captured": False,
            "needs_journal": False,
            "awaiting_departure": False,
        }

        async def _loop() -> None:
            from decimal import Decimal

            from app.database import async_session_factory
            from app.models import Workplace
            from app.services.weighing_service import create_weighing_from_workplace

            while workplace_id in self._workplace_tasks:
                meta = self._workplace_meta[workplace_id]
                terminal_id = meta["terminal_id"]
                config = meta["config"]

                if meta.get("awaiting_departure"):
                    reading_data = self._terminal_readings.get(terminal_id) or {}
                    weight = Decimal(str(reading_data.get("weight", 0)))
                    if weight < config.min_weight_threshold:
                        meta["awaiting_departure"] = False
                        self.get_orchestrator(workplace_id, config).reset(str(workplace_id))
                        async with async_session_factory() as db:
                            workplace = await db.get(Workplace, workplace_id)
                            if workplace:
                                workplace.fsm_state = WeighingState.IDLE.value
                                await db.commit()
                    await asyncio.sleep(0.2)
                    continue

                payload = await self.tick_workplace(
                    workplace_id,
                    terminal_id,
                    config,
                    meta["alpr_provider"],
                )

                if meta.get("needs_journal"):
                    meta["needs_journal"] = False
                    async with async_session_factory() as db:
                        workplace = await db.get(Workplace, workplace_id)
                        if workplace:
                            await create_weighing_from_workplace(db, workplace, meta["operator_id"])

                orch = self.get_orchestrator(workplace_id, config)
                if orch.context.state in (WeighingState.COMPLETED, WeighingState.NEED_DRIVER_CREATE):
                    meta["captured"] = False
                    meta["awaiting_departure"] = True
                    driver = self._terminal_drivers.get(terminal_id)
                    if driver is not None and hasattr(driver, "signal_departure"):
                        driver.signal_departure()
                    async with async_session_factory() as db:
                        workplace = await db.get(Workplace, workplace_id)
                        if workplace:
                            workplace.fsm_state = orch.context.state.value
                            await db.commit()
                elif payload.get("state"):
                    async with async_session_factory() as db:
                        workplace = await db.get(Workplace, workplace_id)
                        if workplace and workplace.fsm_state != payload["state"]:
                            workplace.fsm_state = payload["state"]
                            await db.commit()

                await asyncio.sleep(0.2)

        self._workplace_tasks[workplace_id] = asyncio.create_task(_loop())

    async def stop_workplace_loop(self, workplace_id: uuid.UUID) -> None:
        task = self._workplace_tasks.pop(workplace_id, None)
        self._workplace_meta.pop(workplace_id, None)
        if task:
            task.cancel()
        terminal_id = None
        if workplace_id in self._orchestrators:
            self._orchestrators.pop(workplace_id, None)

    def subscribe(self, channel: str, queue: asyncio.Queue) -> None:
        self._subscribers.setdefault(channel, []).append(queue)

    def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        if channel in self._subscribers:
            self._subscribers[channel] = [q for q in self._subscribers[channel] if q is not queue]

    async def _broadcast(self, channel: str, message: dict) -> None:
        for queue in self._subscribers.get(channel, []):
            await queue.put(message)

    async def test_terminal(self, driver_type: str, config: dict) -> dict:
        driver = create_terminal_driver(driver_type, config)
        try:
            driver.connect()
            result = normalize_test_result(driver.test_connection())
        except Exception as exc:
            return TestResult(
                success=False,
                connected=False,
                message=str(exc),
                error_code="unexpected_error",
            ).model_dump(mode="json")
        finally:
            try:
                driver.disconnect()
            except Exception:
                pass
        return result.model_dump(mode="json")

    async def test_camera(self, connection_type: str, config: dict) -> dict:
        provider = create_camera_provider(connection_type, config)
        provider.connect()
        snapshot = provider.get_snapshot()
        provider.disconnect()
        return {"success": True, "bytes": len(snapshot)}

    async def test_alpr(self, provider_type: str, image: bytes | None = None) -> dict:
        from camera_core.demo import DemoCameraProvider

        provider = create_alpr_provider(provider_type)
        image = image or DemoCameraProvider().get_snapshot()
        candidates = provider.recognize(image)
        return {"candidates": [c.model_dump(mode="json") for c in candidates]}


runtime_manager = RuntimeManager()
