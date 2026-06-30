"""Autoscale Local API — FastAPI runtime."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, cameras, drivers, health, license, terminals, weighings, workplaces, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(license.router)
    app.include_router(terminals.router)
    app.include_router(cameras.router)
    app.include_router(workplaces.router)
    app.include_router(weighings.router)
    app.include_router(drivers.router)
    app.include_router(ws.router)

    return app


app = create_app()
