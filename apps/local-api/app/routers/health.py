"""Health endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.services.license_service import LicenseService
from app.dependencies import get_license_service

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    license_service: LicenseService = Depends(get_license_service),
) -> dict:
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    license_status = await license_service.get_status(db)

    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.app_version,
        "database": "ok" if db_ok else "error",
        "license": license_status,
        "host": settings.host,
        "port": settings.port,
    }
