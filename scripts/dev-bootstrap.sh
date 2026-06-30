#!/usr/bin/env bash
# Bootstrap dev-окружения Autoscale на локальном PostgreSQL 17 (без Docker).
# Linux/macOS/Git Bash. На Windows используйте scripts/dev-bootstrap.ps1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3.12}"
DB_USER="${PGUSER:-$(whoami)}"
DB_HOST="${PGHOST:-127.0.0.1}"
DB_PORT="${PGPORT:-5432}"
LOCAL_DB="${LOCAL_DB_NAME:-autoscale_local}"
OWNER_DB="${OWNER_DB_NAME:-autoscale_owner}"

die() { echo "ERROR: $*" >&2; exit 1; }

urlencode() {
  "$PYTHON" -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$1"
}

if ! command -v "$PYTHON" &>/dev/null; then
  PYTHON=python3
fi
command -v "$PYTHON" >/dev/null || die "Python 3.12+ не найден"
command -v psql >/dev/null || die "psql не найден — установите PostgreSQL 17"
command -v php >/dev/null || die "php не найден"
command -v composer >/dev/null || die "composer не найден"

export PGPASSWORD="${PGPASSWORD:-}"

echo "==> Проверка PostgreSQL"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c 'SELECT 1' >/dev/null \
  || die "Не удаётся подключиться к PostgreSQL как $DB_USER@$DB_HOST:$DB_PORT"

echo "==> Создание БД (если нет)"
for db in "$LOCAL_DB" "$OWNER_DB"; do
  if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db"; then
    echo "  БД $db уже существует"
  else
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$db" \
      || createdb "$db" \
      || die "Создайте БД вручную: createdb $db"
    echo "  Создана БД $db"
  fi
done

echo "==> Python venv и пакеты"
if [ ! -d "$ROOT/.venv" ]; then
  "$PYTHON" -m venv "$ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
pip install -q --upgrade pip
pip install -q \
  "$ROOT/packages/license-core" \
  "$ROOT/packages/hardware-core" \
  "$ROOT/packages/terminal-drivers" \
  "$ROOT/packages/camera-core" \
  "$ROOT/packages/alpr-core" \
  "$ROOT/apps/local-api" \
  psycopg2-binary email-validator \
  "$ROOT/packages/terminal-drivers[hardware]" \
  pytest pytest-asyncio httpx

echo "==> Composer (local-panel, owner-admin)"
for app in local-panel owner-admin; do
  if [ ! -f "$ROOT/apps/$app/vendor/autoload.php" ]; then
    echo "  composer install в apps/$app"
    (cd "$ROOT/apps/$app" && composer install --no-interaction --prefer-dist)
  fi
done

echo "==> Ed25519 ключи"
KEYS_FILE="$ROOT/.env.dev.keys"
if [ ! -f "$KEYS_FILE" ]; then
  "$ROOT/.venv/bin/python" "$ROOT/apps/local-api/scripts/generate_keys.py" > "$KEYS_FILE"
  echo "  Ключи сохранены в $KEYS_FILE"
fi
# shellcheck disable=SC1090
source "$KEYS_FILE"
[ -n "${LICENSE_SIGNING_PRIVATE_KEY:-}" ] || die "LICENSE_SIGNING_PRIVATE_KEY пуст в $KEYS_FILE"
[ -n "${LICENSE_PUBLIC_KEY:-}" ] || die "LICENSE_PUBLIC_KEY пуст в $KEYS_FILE"

echo "==> local-api .env"
API_ENV="$ROOT/apps/local-api/.env"
if [ ! -f "$API_ENV" ]; then
  cp "$ROOT/apps/local-api/.env.example" "$API_ENV"
fi
if [ -n "${PGPASSWORD:-}" ]; then
  ENC_PASS="$(urlencode "$PGPASSWORD")"
  DB_URL="postgresql+asyncpg://${DB_USER}:${ENC_PASS}@${DB_HOST}:${DB_PORT}/${LOCAL_DB}"
else
  DB_URL="postgresql+asyncpg://${DB_USER}@${DB_HOST}:${DB_PORT}/${LOCAL_DB}"
fi
if grep -q "^DATABASE_URL=" "$API_ENV"; then
  sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$DB_URL|" "$API_ENV"
else
  echo "DATABASE_URL=$DB_URL" >> "$API_ENV"
fi
if grep -q "^LICENSE_PUBLIC_KEY=" "$API_ENV"; then
  sed -i.bak "s|^LICENSE_PUBLIC_KEY=.*|LICENSE_PUBLIC_KEY=$LICENSE_PUBLIC_KEY|" "$API_ENV"
else
  echo "LICENSE_PUBLIC_KEY=$LICENSE_PUBLIC_KEY" >> "$API_ENV"
fi
CORS_ORIGINS="http://127.0.0.1:8081,http://localhost:8081,http://127.0.0.1:8080,http://localhost:8080"
if grep -q "^CORS_ORIGINS=" "$API_ENV"; then
  sed -i.bak "s|^CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_ORIGINS|" "$API_ENV"
else
  echo "CORS_ORIGINS=$CORS_ORIGINS" >> "$API_ENV"
fi
rm -f "$API_ENV.bak"

echo "==> Alembic migrate + seed"
cd "$ROOT/apps/local-api"
export DEV_LICENSE_PRIVATE_KEY="$LICENSE_SIGNING_PRIVATE_KEY"
export LICENSE_SIGNING_PRIVATE_KEY
export LICENSE_PUBLIC_KEY
"$ROOT/.venv/bin/alembic" upgrade head
"$ROOT/.venv/bin/python" scripts/seed_demo.py

echo "==> Проверка таблиц в $LOCAL_DB"
TABLE_COUNT="$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$LOCAL_DB" -tAc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")"
[ "${TABLE_COUNT:-0}" -gt 0 ] || die "$LOCAL_DB не содержит таблиц после миграции"
echo "  Найдено таблиц: $TABLE_COUNT"

echo "==> owner-admin .env"
OWNER_ENV="$ROOT/apps/owner-admin/.env"
if [ ! -f "$OWNER_ENV" ]; then
  cp "$ROOT/apps/owner-admin/.env.example" "$OWNER_ENV"
  (cd "$ROOT/apps/owner-admin" && php artisan key:generate --force)
fi
for kv in "DB_CONNECTION=pgsql" "DB_USERNAME=$DB_USER" "DB_PASSWORD=${PGPASSWORD:-}" \
          "DB_HOST=$DB_HOST" "DB_PORT=$DB_PORT" "DB_DATABASE=$OWNER_DB" \
          "LICENSE_SIGNING_PRIVATE_KEY=$LICENSE_SIGNING_PRIVATE_KEY" "LICENSE_PUBLIC_KEY=$LICENSE_PUBLIC_KEY"; do
  key="${kv%%=*}"
  val="${kv#*=}"
  if grep -q "^${key}=" "$OWNER_ENV"; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$OWNER_ENV"
  else
    echo "${key}=${val}" >> "$OWNER_ENV"
  fi
done
rm -f "$OWNER_ENV.bak"

echo "==> owner-admin migrate + seed"
cd "$ROOT/apps/owner-admin"
php artisan migrate --force
php artisan db:seed --force
php artisan optimize:clear

echo "==> local-panel .env"
PANEL_ENV="$ROOT/apps/local-panel/.env"
if [ ! -f "$PANEL_ENV" ]; then
  cp "$ROOT/apps/local-panel/.env.example" "$PANEL_ENV"
  (cd "$ROOT/apps/local-panel" && php artisan key:generate --force)
fi
for kv in "LOCAL_API_URL=http://127.0.0.1:8000" "LOCAL_API_WS_URL=ws://127.0.0.1:8000" "SESSION_DRIVER=file" "APP_URL=http://127.0.0.1:8081" "DB_CONNECTION=sqlite"; do
  key="${kv%%=*}"
  val="${kv#*=}"
  if grep -q "^${key}=" "$PANEL_ENV" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$PANEL_ENV"
  else
    echo "${key}=${val}" >> "$PANEL_ENV"
  fi
done
rm -f "$PANEL_ENV.bak"

echo "==> local-panel sqlite migrate + cache clear"
PANEL_DIR="$ROOT/apps/local-panel"
if [ ! -f "$PANEL_DIR/database/database.sqlite" ]; then
  touch "$PANEL_DIR/database/database.sqlite"
  echo "  Created database/database.sqlite"
fi
(cd "$PANEL_DIR" && php artisan migrate --force && php artisan optimize:clear)

echo ""
echo "Bootstrap завершён."
echo "Далее: ./scripts/demo-smoke.sh  (после запуска сервисов)"
echo "Запуск сервисов — см. docs/08-demo-runbook.md"
