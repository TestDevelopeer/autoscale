"""Demo seed data и demo license."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from license_core.validator import LicenseSigner
from license_core.fingerprint import collect_machine_fingerprint
from license_core.models import LicenseLimits, LicensePayload, LicenseStatus
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session_factory
from app.models import Camera, LicenseState, Terminal, User, Workplace, WorkplaceCamera
from app.services.auth_service import hash_password


async def seed() -> None:
    settings = get_settings()
    async with async_session_factory() as db:
        user = await db.scalar(select(User).where(User.email == "operator@demo.local"))
        if user is None:
            user = User(email="operator@demo.local", name="Demo Operator", password_hash=hash_password("demo"))
            db.add(user)

        terminal = await db.scalar(select(Terminal).where(Terminal.name == "DEMO Terminal"))
        demo_config = {
            "target_weight": 15000,
            "ramp_seconds": 3,
            "stable_after": 4,
            "departure_seconds": 2,
        }
        if terminal is None:
            terminal = Terminal(name="DEMO Terminal", driver_type="demo", config=demo_config)
            db.add(terminal)
            await db.flush()
        else:
            terminal.config = demo_config

        camera = await db.scalar(select(Camera).where(Camera.name == "DEMO Camera"))
        if camera is None:
            camera = Camera(name="DEMO Camera", connection_type="demo", config={}, alpr_provider="demo")
            db.add(camera)
            await db.flush()

        workplace = await db.scalar(select(Workplace).where(Workplace.name == "Demo Lane"))
        if workplace is None:
            workplace = Workplace(
                name="Demo Lane",
                terminal_id=terminal.id,
                alpr_provider="demo",
                min_weight_threshold=Decimal("100"),
                stable_seconds=Decimal("1"),
                auto_confirm=True,
            )
            db.add(workplace)
            await db.flush()
            db.add(WorkplaceCamera(workplace_id=workplace.id, camera_id=camera.id))

        await db.commit()

    # Demo license если есть private key в env (dev only)
    import os

    priv = os.environ.get("LICENSE_SIGNING_PRIVATE_KEY") or os.environ.get("DEV_LICENSE_PRIVATE_KEY")
    pub = settings.license_public_key or os.environ.get("LICENSE_PUBLIC_KEY")
    if priv and pub:
        signer = LicenseSigner(priv)
        payload = LicensePayload(
            license_id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            organization_name="Demo Organization",
            modules=[
                "core", "terminals", "cameras", "alpr", "weighing_journal",
                "drivers_registry", "workplaces", "reports_basic", "api_access", "multi_workplace",
            ],
            limits=LicenseLimits(max_users=10, max_workplaces=5, max_terminals=10, max_cameras=20),
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            grace_days=14,
            offline_until=datetime.now(timezone.utc) + timedelta(days=180),
            machine_fingerprint=collect_machine_fingerprint(),
            issued_at=datetime.now(timezone.utc),
            status=LicenseStatus.ACTIVE,
        )
        signed = signer.sign(payload)
        from pathlib import Path

        path = Path(settings.license_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(signed.model_dump_json(indent=2), encoding="utf-8")

        async with async_session_factory() as db:
            state = await db.scalar(select(LicenseState).where(LicenseState.id == 1))
            if state is None:
                state = LicenseState(id=1)
                db.add(state)
            state.license_id = payload.license_id
            state.status = "active"
            state.raw_file = signed.model_dump_json()
            await db.commit()

    print("Seed completed: operator@demo.local / demo")


if __name__ == "__main__":
    asyncio.run(seed())
