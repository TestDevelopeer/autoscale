#!/usr/bin/env python3
"""Hardware debug: чтение весового терминала без журнала и FSM."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Добавляем packages в path при запуске из репозитория
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "packages" / "terminal-drivers") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "terminal-drivers"))

from terminal_drivers.probe.runner import TerminalProbeRunner, normalize_driver_name
from terminal_drivers.probe.serial_io import SerialSettings


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Hardware probe весового терминала (без journal/FSM/panel)",
    )
    p.add_argument("--driver", required=True, help="keli-d2008fa | cas-ci-200a | demo")
    p.add_argument("--port", default="", help="COM-порт, например COM3 или /dev/ttyUSB0")
    p.add_argument("--baudrate", type=int, default=None)
    p.add_argument("--parity", default=None, help="none|even|odd (N/E/O)")
    p.add_argument("--stop-bits", type=int, default=1)
    p.add_argument("--data-bits", type=int, default=8)
    p.add_argument("--timeout", type=float, default=2.0, help="Timeout чтения, сек")
    p.add_argument("--device-id", type=int, default=None, help="Modbus slave ID (Keli)")
    p.add_argument("--duration", type=float, default=10.0, help="Длительность probe, сек")
    p.add_argument("--interval", type=float, default=0.2, help="Интервал опроса, сек")
    p.add_argument("--out", default="", help="Путь к JSON-отчёту")
    p.add_argument("--fixture", action="store_true", help="Без COM: parser self-test на фикстурах")
    return p


def default_baudrate(driver: str) -> int:
    return 19200 if driver == "cas_ci200a" else 9600


def default_parity(driver: str) -> str:
    return "N"


def default_device_id(driver: str) -> int:
    return 0 if driver == "cas_ci200a" else 1


def fixture_frames(driver: str) -> list[str | bytes]:
    if driver == "keli_d2008fa":
        return ["ST 00015000", b"\x01\x03\x04ST 00015000", "?? garbage"]
    if driver == "cas_ci200a":
        return ["ST     15230 kg", "US     12000 kg", "no weight here"]
    return []


def print_report(report) -> None:
    data = report.to_dict()
    print(f"driver: {data['driver']}")
    print(f"connected: {data['connected']}")
    print(f"success: {data['success_count']}  failures: {data['failure_count']}")
    print(f"summary: {data['summary']}")
    if data["parsed_samples"]:
        last = data["parsed_samples"][-1]
        print(
            f"last parsed: weight={last.get('weight')} stable={last.get('stable')} "
            f"unit={last.get('unit')} status={last.get('status')}"
        )
    if data["raw_samples"]:
        print(f"last raw: {data['raw_samples'][-1].get('raw', '')[:120]}")
    for err in data["errors"][:5]:
        print(f"ERROR [{err.get('code')}]: {err.get('message')}")
    for warn in data["warnings"][:3]:
        print(f"WARN [{warn.get('code')}]: {warn.get('message')}")
    print(f"next: {data['recommended_next_action']}")


def main() -> int:
    args = build_parser().parse_args()
    try:
        driver = normalize_driver_name(args.driver)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.fixture:
        settings = SerialSettings(port="FIXTURE", baudrate=0, timeout=args.timeout)
        runner = TerminalProbeRunner(driver, settings)
        report = runner.run_fixture(fixture_frames(driver), duration=args.duration)
        print_report(report)
        if args.out:
            report.save(args.out)
            print(f"saved: {args.out}")
        return 0 if report.success_count > 0 else 1

    if driver == "demo":
        settings = SerialSettings(port="DEMO", baudrate=0, timeout=args.timeout)
        runner = TerminalProbeRunner(driver, settings)
        report = runner.run(duration=args.duration, poll_interval=args.interval)
        print_report(report)
        if args.out:
            report.save(args.out)
        return 0

    if not args.port:
        print(
            "ERROR: укажите --port (например --port COM3). "
            "Probe не создаёт записей в журнале.",
            file=sys.stderr,
        )
        return 2

    settings = SerialSettings(
        port=args.port,
        baudrate=args.baudrate if args.baudrate is not None else default_baudrate(driver),
        parity=args.parity if args.parity is not None else default_parity(driver),
        stop_bits=args.stop_bits,
        data_bits=args.data_bits,
        timeout=args.timeout,
        device_id=args.device_id if args.device_id is not None else default_device_id(driver),
    )

    runner = TerminalProbeRunner(driver, settings)
    report = runner.run(duration=args.duration, poll_interval=args.interval)
    print_report(report)

    if args.out:
        report.save(args.out)
        print(f"saved: {args.out}")

    return 0 if report.connected and report.success_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
