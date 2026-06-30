"""Фабрика драйверов терминалов."""

from __future__ import annotations

from typing import Any

from hardware_core.terminal import TerminalDriver
from terminal_drivers.cas_ci200a.driver import CasCi200aDriver
from terminal_drivers.demo.driver import DemoTerminalDriver
from terminal_drivers.keli_d2008fa.driver import KeliD2008faDriver

DRIVER_TYPES = {
    "demo": DemoTerminalDriver,
    "keli_d2008fa": KeliD2008faDriver,
    "cas_ci200a": CasCi200aDriver,
}


def create_terminal_driver(driver_type: str, config: dict[str, Any]) -> TerminalDriver:
    cls = DRIVER_TYPES.get(driver_type)
    if cls is None:
        raise ValueError(f"Unknown terminal driver type: {driver_type}")
    return cls(config)
