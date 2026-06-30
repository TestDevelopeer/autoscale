"""Тесты demo-провайдеров и hardening."""

from __future__ import annotations

import time
from decimal import Decimal

from alpr_core.demo import DemoAlprProvider
from terminal_drivers.demo.driver import DemoTerminalDriver


def test_demo_terminal_reaches_stable_target_weight():
    driver = DemoTerminalDriver({
        "target_weight": 15000,
        "ramp_seconds": 0.5,
        "stable_after": 1.0,
    })
    driver.connect()
    deadline = time.monotonic() + 3.0
    stable = False
    weight = Decimal("0")
    while time.monotonic() < deadline:
        reading = driver.get_current_weight()
        weight = reading.weight
        stable = reading.stable
        if stable and weight >= Decimal("14900"):
            break
        time.sleep(0.1)
    driver.disconnect()
    assert stable
    assert Decimal("14900") <= weight <= Decimal("15100")


def test_demo_terminal_departure_drops_weight():
    driver = DemoTerminalDriver({
        "target_weight": 15000,
        "ramp_seconds": 0.1,
        "stable_after": 0.2,
        "departure_seconds": 0.5,
    })
    driver.connect()
    time.sleep(0.3)
    driver.signal_departure()
    time.sleep(0.6)
    reading = driver.get_current_weight()
    driver.disconnect()
    assert reading.weight == Decimal("0")
    assert reading.stable is True


def test_demo_alpr_returns_a123bc77():
    provider = DemoAlprProvider()
    candidates = provider.recognize(b"fake-image")
    assert len(candidates) == 1
    assert candidates[0].plate_normalized == "A123BC77"
    assert candidates[0].confidence >= 0.9


def test_cameras_alpr_test_route_not_shadowed():
    """Маршрут /api/cameras/alpr/test не должен матчиться как {camera_id}."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/cameras/alpr/test?provider=demo")
    assert response.status_code in (401, 403)
