# 06 — Критерии приёмки MVP

## Общие условия

- Окружение: **локальный PostgreSQL 17** на `127.0.0.1:5432` (без Docker).
- Две БД: `autoscale_local` (local-api), `autoscale_owner` (owner-admin).
- Bootstrap: `./scripts/dev-bootstrap.sh`
- Demo mode: DEMO terminal + DEMO camera + DemoAlprProvider.
- Лицензия: valid license с modules `core`, `terminals`, `cameras`, `alpr`, `workplaces`, `weighing_journal`, `drivers_registry`.

---

## URL и учётные данные (dev)

| Сервис | URL |
|--------|-----|
| local-panel (login) | http://127.0.0.1:8080/login |
| local-panel (admin) | http://127.0.0.1:8080/admin |
| local-api | http://127.0.0.1:8000 |
| owner-admin | http://127.0.0.1:8090/admin |
| API docs | http://127.0.0.1:8000/docs |

| Роль | Email | Password |
|------|-------|----------|
| Оператор (local) | operator@demo.local | demo |
| Владелец (owner) | owner@demo.local | demo |

---

## Команды запуска

### Dev environment

```bash
# Однократно
createdb autoscale_local
createdb autoscale_owner

# Bootstrap: venv, ключи, migrate, seed
chmod +x scripts/dev-bootstrap.sh
./scripts/dev-bootstrap.sh

# Терминал 1
cd apps/local-api && ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Терминал 2
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8080

# Терминал 3
cd apps/owner-admin && php artisan serve --host=127.0.0.1 --port=8090
```

### Тесты

```bash
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

### Smoke

```bash
curl -s http://127.0.0.1:8000/api/health | jq .
```

---

## Checklist приёмки

### A. Инфраструктура

- [ ] `./scripts/dev-bootstrap.sh` завершается без ошибок
- [ ] `GET /api/health` → 200, `status: ok`
- [ ] local-api слушает только `127.0.0.1` по умолчанию

### B. Лицензирование

- [ ] owner-admin: создать организацию, лицензию, назначить modules
- [ ] Online activation: local-api → owner-admin → signed file → active
- [ ] Offline: activation request → owner issue → import → active
- [ ] Invalid signature → reject import
- [ ] Module `alpr` off → нет auto recognition, cameras work

### C. Auth

- [ ] Login operator → token → доступ к API
- [ ] Panel session использует API token

### D–J

См. полный checklist в предыдущих версиях; детали runtime — в `docs/07-mvp-acceptance-report.md`.

---

## Demo scenario (E2E script)

1. `./scripts/dev-bootstrap.sh`
2. Запустить local-api, local-panel, owner-admin.
3. Open http://127.0.0.1:8080/login → `operator@demo.local` / `demo`
4. Workplaces → Demo Lane → start
5. Журнал → запись с plate A123BC77, weight ~15000 kg (через ~12 сек)

---

## Вне MVP (не блокирует приёмку)

- Docker
- Production Windows installer (см. `installer/`)
- RTSP camera (stub)
- WS `/ws/cameras/{id}`
