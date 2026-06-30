"""Формат отчёта terminal probe."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ProbeReport:
    driver: str
    port_settings: dict[str, Any]
    started_at: str
    duration: float
    connected: bool = False
    raw_samples: list[dict[str, Any]] = field(default_factory=list)
    parsed_samples: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    summary: str = ""
    recommended_next_action: str = ""

    def add_raw(self, raw: str | bytes, ts: datetime | None = None) -> None:
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        self.raw_samples.append({
            "at": (ts or datetime.now(timezone.utc)).isoformat(),
            "raw": text,
            "hex": raw.hex() if isinstance(raw, bytes) else None,
        })

    def add_parsed(self, reading_dict: dict[str, Any], ts: datetime | None = None) -> None:
        self.parsed_samples.append({
            "at": (ts or datetime.now(timezone.utc)).isoformat(),
            **reading_dict,
        })

    def add_error(self, diagnostic: dict[str, Any]) -> None:
        self.errors.append(diagnostic)
        self.failure_count += 1

    def add_warning(self, diagnostic: dict[str, Any]) -> None:
        self.warnings.append(diagnostic)

    def record_success(self) -> None:
        self.success_count += 1

    def finalize(self) -> None:
        total = self.success_count + self.failure_count
        if self.success_count > 0 and self.failure_count == 0:
            self.summary = f"Успешно: {self.success_count} чтений за {self.duration}s"
            self.recommended_next_action = "Подключите терминал в panel и запустите test_connection."
        elif self.success_count > 0:
            self.summary = f"Частичный успех: {self.success_count}/{total} чтений"
            self.recommended_next_action = "Сверьте raw samples с документацией; уточните register map / формат кадра."
        elif self.failure_count > 0:
            self.summary = f"Ошибки: {self.failure_count} за {self.duration}s"
            self.recommended_next_action = "Проверьте COM-настройки и кабель; повторите probe с --duration 60."
        else:
            self.summary = "Нет успешных чтений"
            self.recommended_next_action = "Терминал молчит — проверьте порт, питание и baudrate/parity."

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver": self.driver,
            "port_settings": self.port_settings,
            "started_at": self.started_at,
            "duration": self.duration,
            "connected": self.connected,
            "raw_samples": self.raw_samples,
            "parsed_samples": self.parsed_samples,
            "errors": self.errors,
            "warnings": self.warnings,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "summary": self.summary,
            "recommended_next_action": self.recommended_next_action,
        }

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
