"""Конфигурация local-api."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Autoscale Local API"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = "postgresql+asyncpg://autoscale:autoscale@127.0.0.1:5432/autoscale_local"

    license_public_key: str = ""
    license_file_path: str = "./data/license.lic"
    license_state_path: str = "./data/license_state.json"

    owner_admin_url: str = "http://127.0.0.1:8090"
    cors_origins: str = "http://127.0.0.1:8080"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 480

    allow_lan: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
