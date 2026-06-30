"""Сбор machine fingerprint установки."""

from __future__ import annotations

import hashlib
import platform
import socket
import uuid


def collect_machine_fingerprint() -> str:
    """Стабильный fingerprint для привязки лицензии."""
    parts: list[str] = [
        platform.system(),
        platform.machine(),
        socket.gethostname(),
    ]

    if platform.system() == "Windows":
        try:
            parts.append(str(uuid.getnode()))
        except OSError:
            pass
    else:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                with open(path, encoding="utf-8") as f:
                    parts.append(f.read().strip())
                    break
            except OSError:
                continue

    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
