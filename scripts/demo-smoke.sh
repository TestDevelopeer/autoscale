#!/usr/bin/env bash
# Smoke-проверка demo-окружения Autoscale. Exit 0 = demo готово.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${API_URL:-http://127.0.0.1:8000}"
PANEL="${PANEL_URL:-http://127.0.0.1:8080}"
OWNER="${OWNER_URL:-http://127.0.0.1:8090}"
FULL_CYCLE="${DEMO_SMOKE_FULL:-0}"

PYTHON="$ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON=python3

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

echo "==> local-api health"
HEALTH=$(curl -sf "$API/api/health") || fail "local-api недоступен на $API"
echo "$HEALTH" | "$PYTHON" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("status")=="ok", d' \
  || fail "health status != ok"
ok "health"

LICENSE_VALID=$(echo "$HEALTH" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin).get("license",{}).get("valid",False))')
[ "$LICENSE_VALID" = "True" ] || fail "лицензия не valid в health"
ok "license valid"

echo "==> local-panel"
curl -sf -o /dev/null "$PANEL/login" || fail "local-panel недоступен на $PANEL/login"
ok "panel /login"

echo "==> owner-admin"
curl -sf -o /dev/null "$OWNER" || curl -sf -o /dev/null "$OWNER/admin" || fail "owner-admin недоступен на $OWNER"
ok "owner-admin"

echo "==> API auth + resources"
LOGIN=$(curl -sf -X POST "$API/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"operator@demo.local","password":"demo"}') \
  || fail "login operator@demo.local"
TOKEN=$(echo "$LOGIN" | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"

curl -sf "$API/api/license/status" -H "$AUTH" | "$PYTHON" -c \
  'import json,sys; d=json.load(sys.stdin); assert d.get("valid"), d; mods=set(d.get("modules",[])); need={"core","terminals","cameras","alpr","workplaces","weighing_journal"}; assert need<=mods, mods' \
  || fail "license modules incomplete"
ok "license modules"

TERMINALS=$(curl -sf "$API/api/terminals" -H "$AUTH")
echo "$TERMINALS" | "$PYTHON" -c 'import json,sys; t=json.load(sys.stdin); assert any(x.get("name")=="DEMO Terminal" for x in t), t' \
  || fail "DEMO Terminal не найден"
ok "DEMO Terminal"

CAMERAS=$(curl -sf "$API/api/cameras" -H "$AUTH")
echo "$CAMERAS" | "$PYTHON" -c 'import json,sys; c=json.load(sys.stdin); assert any(x.get("name")=="DEMO Camera" for x in c), c' \
  || fail "DEMO Camera не найдена"
ok "DEMO Camera"

WORKPLACES=$(curl -sf "$API/api/workplaces" -H "$AUTH")
WP_ID=$(echo "$WORKPLACES" | "$PYTHON" -c 'import json,sys; w=json.load(sys.stdin); lane=next((x for x in w if x.get("name")=="Demo Lane"), None); assert lane, w; print(lane["id"])') \
  || fail "Demo Lane не найден"
ok "Demo Lane ($WP_ID)"

echo "$TERMINALS" | "$PYTHON" -c 'import json,sys; t=json.load(sys.stdin); demo=next(x for x in t if x["name"]=="DEMO Terminal"); print(demo["id"])' > /tmp/autoscale_demo_terminal_id.$$
TID=$(cat /tmp/autoscale_demo_terminal_id.$$)
rm -f /tmp/autoscale_demo_terminal_id.$$
curl -sf -X POST "$API/api/terminals/$TID/test" -H "$AUTH" >/dev/null || fail "terminal test failed"
ok "DEMO terminal test"

curl -sf -X POST "$API/api/cameras/alpr/test?provider=demo" -H "$AUTH" | "$PYTHON" -c \
  'import json,sys; d=json.load(sys.stdin); c=d.get("candidates",[]); assert c and c[0].get("plate_normalized")=="A123BC77", d' \
  || fail "demo ALPR != A123BC77"
ok "demo ALPR A123BC77"

JOURNAL=$(curl -sf "$API/api/weighings" -H "$AUTH")
COUNT=$(echo "$JOURNAL" | "$PYTHON" -c 'import json,sys; print(len(json.load(sys.stdin)))')

if [ "$FULL_CYCLE" = "1" ]; then
  echo "==> full demo cycle (start workplace, wait ~10s)"
  curl -sf -X POST "$API/api/workplaces/$WP_ID/start" -H "$AUTH" >/dev/null
  sleep 10
  JOURNAL=$(curl -sf "$API/api/weighings" -H "$AUTH")
  echo "$JOURNAL" | "$PYTHON" -c \
    'import json,sys; j=json.load(sys.stdin); assert j, "journal empty"; r=j[0]; assert r.get("plate_normalized")=="A123BC77", r; w=float(r.get("weight",0)); assert 14000<=w<=16000, r' \
    || fail "journal record missing or invalid after full cycle"
  ok "journal record after full cycle"
else
  curl -sf "$API/api/weighings" -H "$AUTH" >/dev/null || fail "journal endpoint"
  ok "journal endpoint ($COUNT записей)"
  if [ "$COUNT" -gt 0 ]; then
    echo "$JOURNAL" | "$PYTHON" -c \
      'import json,sys; r=json.load(sys.stdin)[0]; assert r.get("plate_normalized"), r; print("  последняя:", r.get("plate_normalized"), r.get("weight"))'
  fi
fi

echo ""
echo "Demo smoke: PASS"
