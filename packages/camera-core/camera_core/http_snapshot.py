"""HTTP snapshot camera provider."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from hardware_core.camera import StreamStatus
from hardware_core.health import HealthReport, HealthStatus


class HttpSnapshotProvider:
    def __init__(self, config: dict[str, Any]) -> None:
        self._url = config["url"]
        self._username = config.get("username")
        self._password = config.get("password")
        self._timeout = float(config.get("timeout_ms", 5000)) / 1000
        self._connected = False
        self._last_error: str | None = None

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def get_snapshot(self) -> bytes:
        auth = None
        if self._username and self._password:
            auth = (self._username, self._password)
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(self._url, auth=auth)
            response.raise_for_status()
            return response.content

    def get_stream_status(self) -> StreamStatus:
        if not self._connected:
            return StreamStatus.IDLE
        if self._last_error:
            return StreamStatus.ERROR
        return StreamStatus.RUNNING

    def health(self) -> HealthReport:
        try:
            self.get_snapshot()
            return HealthReport(
                status=HealthStatus.OK,
                message="HTTP snapshot OK",
                last_success_at=datetime.now(timezone.utc),
            )
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            return HealthReport(
                status=HealthStatus.ERROR,
                message="HTTP snapshot failed",
                last_error=str(exc),
            )

    def reconnect(self) -> None:
        self._last_error = None
        self.connect()
