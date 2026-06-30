"""License endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from license_core.models import SignedLicenseFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_license_service
from app.models import User
from app.services.license_service import LicenseService

router = APIRouter(prefix="/api/license", tags=["license"])


class OnlineActivateRequest(BaseModel):
    license_id: str
    activation_code: str


@router.get("/status")
async def license_status(
    db: AsyncSession = Depends(get_db),
    license_service: LicenseService = Depends(get_license_service),
) -> dict:
    return await license_service.get_status(db)


@router.post("/activate-online")
async def activate_online(
    body: OnlineActivateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    license_service: LicenseService = Depends(get_license_service),
) -> dict:
    try:
        return await license_service.activate_online(db, body.license_id, body.activation_code, user.id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/offline/request")
async def offline_request(
    license_service: LicenseService = Depends(get_license_service),
) -> dict:
    return await license_service.create_offline_request()


@router.post("/offline/import")
async def offline_import(
    body: SignedLicenseFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    license_service: LicenseService = Depends(get_license_service),
) -> dict:
    try:
        return await license_service.import_license(db, body, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
