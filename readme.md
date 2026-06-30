# Autoscale MVP

Offline-first система автоматизации взвешивания на автомобильных весах.

**Статус:** `ACCEPTED_FOR_DEMO` — см. [`docs/10-demo-freeze.md`](docs/10-demo-freeze.md)

## Demo quick start

```bash
./scripts/dev-bootstrap.sh
./scripts/demo-smoke.sh
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
```

Запустите сервисы (см. [docs/08-demo-runbook.md](docs/08-demo-runbook.md)), затем откройте:

- http://127.0.0.1:8080/login
- `operator@demo.local` / `demo`

## Требования

- **PostgreSQL 17** на `localhost:5432` (две БД: `autoscale_local`, `autoscale_owner`)
- **Python 3.12+**
- **PHP 8.4+**, Composer
- Без Docker

## Быстрый старт

```bash
# Однократно: создать БД
createdb autoscale_local
createdb autoscale_owner

# Bootstrap: venv, ключи, миграции, seed
chmod +x scripts/dev-bootstrap.sh
./scripts/dev-bootstrap.sh

# Терминал 1 — local-api
cd apps/local-api
../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Терминал 2 — local-panel
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8080

# Терминал 3 — owner-admin
cd apps/owner-admin && php artisan serve --host=127.0.0.1 --port=8090
```

## URL

| Сервис | URL |
|--------|-----|
| local-panel (login) | http://127.0.0.1:8080/login |
| local-panel (admin) | http://127.0.0.1:8080/admin |
| local-api | http://127.0.0.1:8000 |
| owner-admin | http://127.0.0.1:8090/admin |

**Demo:** `operator@demo.local` / `demo`

## Тесты

```bash
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

Документация: [docs/08-demo-runbook.md](docs/08-demo-runbook.md)
