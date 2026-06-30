"""Health reports для оборудования."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class HealthReport(BaseModel):
    status: HealthStatus = HealthStatus.OK
    message: str = ""
    last_success_at: datetime | None = None
    last_error: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
