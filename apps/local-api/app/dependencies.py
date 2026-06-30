"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.models import User
from app.services.auth_service import get_user_from_token
from app.services.license_service import LicenseService

security = HTTPBearer(auto_error=False)


def get_license_service(settings: Settings = Depends(get_settings)) -> LicenseService:
    return LicenseService(settings)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    user = await get_user_from_token(db, settings, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    return user


def require_module(module: str):
    async def _checker(license_service: LicenseService = Depends(get_license_service)) -> None:
        try:
            license_service.require_module(module)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _checker
