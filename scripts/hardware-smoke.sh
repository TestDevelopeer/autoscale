#!/usr/bin/env bash
# Hardware smoke: terminal probe на реальном COM (опционально).
# Не требует local-panel и не создаёт записей в журнале.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
PROBE="$ROOT/apps/local-api/scripts/terminal_probe.py"
DRIVER="${TERMINAL_PROBE_DRIVER:-}"
PORT="${TERMINAL_PROBE_PORT:-}"
DURATION="${TERMINAL_PROBE_DURATION:-15}"
OUT="${TERMINAL_PROBE_OUT:-}"

if [ ! -x "$PYTHON" ]; then
  PYTHON=python3
fi

if [ -z "$DRIVER" ]; then
  echo "SKIP: укажите TERMINAL_PROBE_DRIVER=keli-d2008fa или cas-ci-200a"
  echo "Пример: TERMINAL_PROBE_DRIVER=keli-d2008fa TERMINAL_PROBE_PORT=COM3 $0"
  exit 0
fi

if [ -z "$PORT" ]; then
  echo "SKIP: укажите TERMINAL_PROBE_PORT (например COM3 или /dev/ttyUSB0)"
  echo "Пример: TERMINAL_PROBE_DRIVER=$DRIVER TERMINAL_PROBE_PORT=COM3 $0"
  exit 0
fi

BAUDRATE="${TERMINAL_PROBE_BAUDRATE:-}"
PARITY="${TERMINAL_PROBE_PARITY:-}"
TIMEOUT="${TERMINAL_PROBE_TIMEOUT:-2}"
OUT_ARG=""
if [ -n "$OUT" ]; then
  OUT_ARG="--out $OUT"
elif [ -n "${TERMINAL_PROBE_SAVE:-}" ]; then
  mkdir -p "$ROOT/storage/probes"
  OUT_ARG="--out $ROOT/storage/probes/${DRIVER}-${PORT//\//_}-$(date +%Y%m%d-%H%M%S).json"
fi

CMD=("$PYTHON" "$PROBE" "--driver" "$DRIVER" "--port" "$PORT" "--duration" "$DURATION" "--timeout" "$TIMEOUT")
[ -n "$BAUDRATE" ] && CMD+=(--baudrate "$BAUDRATE")
[ -n "$PARITY" ] && CMD+=(--parity "$PARITY")
[ -n "$OUT_ARG" ] && CMD+=($OUT_ARG)

echo "==> hardware probe: $DRIVER @ $PORT"
"${CMD[@]}"
echo "Hardware smoke: PASS"
