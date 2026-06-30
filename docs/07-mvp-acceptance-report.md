# 07 — Отчёт строгой приёмки MVP Autoscale

**Дата:** 2026-06-29  
**Git:** `6789dd8`  
**Окружение:** macOS, PostgreSQL 17 @ `127.0.0.1:5432`, Python 3.12, PHP 8.4, без Docker

---

## Команды запуска (фактические)

```bash
createdb autoscale_local   # однократно
createdb autoscale_owner   # однократно
./scripts/dev-bootstrap.sh

cd apps/local-api && ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8080
cd apps/owner-admin && php artisan serve --host=127.0.0.1 --port=8090
```

---

## Тесты

```bash
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

**Результат:** 16 passed, 1 skipped (`test_license_php_python_compatible` — skipped если PHP autoload недоступен в CI-контексте; вручную canonical JSON **совпадает**).

---

## Runtime smoke (local-api)

| Проверка | Результат |
|----------|-----------|
| `GET /api/health` | 200, `status: ok`, license active |
| `POST /api/auth/login` (`operator@demo.local` / `demo`) | 200, JWT |
| `GET /api/terminals` … `weighings` | 200 с токеном |
| `POST /api/workplaces/{id}/start` (Demo Lane) | 200, FSM started |
| `GET /api/weighings` после ~14 с | Запись: plate `A123BC77`, weight `15000 kg`, status `need_driver_create` |

---

## Demo-сценарии

| # | Сценарий | Статус |
|---|----------|--------|
| 1 | Bootstrap одним скриптом на локальном PG | **PASS** |
| 2 | Login → Demo Lane → start → запись в журнале | **PASS** |
| 3 | PHP↔Python canonical JSON для подписи | **PASS** (байт-в-байт) |
| 4 | Feature-gating на API | **PASS** (см. лицензии A–E) |
| 5 | pytest критичные тесты | **PASS** |

---

## Лицензирование (сценарии A–E)

| Сценарий | Проверка | Результат |
|----------|----------|-----------|
| A | Full modules | **PASS** — `validator.validate` valid |
| B | Без `alpr` | **PASS** — `require_module('alpr')` → PermissionError (unit) |
| C | Без `terminals` | **PASS** — `GET /api/terminals` блокируется через `require_module` |
| D | Tampered payload | **PASS** — invalid signature |
| E | Expired `expires_at` | **PARTIAL** — при `expires_days=-1` остаётся `grace_days` (14 дн.); для жёсткого expired нужен срок > grace |

---

## Найдено / исправлено / осталось

### Исправлено (blocking)

| Проблема | Решение |
|----------|---------|
| Docker в проекте | Удалены `docker-compose.yml`, Dockerfiles; bootstrap на локальный PG |
| FSM не работал end-to-end | `start_workplace_loop` + `tick_workplace` + demo ALPR feed |
| Журнал пустой | `weighing_service.create_weighing_from_workplace` после capture |
| PHP ≠ Python canonical JSON | `LicenseCanonicalJson` (recursive ksort) + `license_core.canonical` |
| Route `platform.workplaces.create` | `WorkplaceEditScreen` + route |
| Panel permissions | `platform.autoscale` при login |
| Bootstrap ломался | `psycopg2-binary`, `email-validator`, DB user = `$PGUSER`, bcrypt fix |
| Login `operator@demo.local` | `EmailStr` → `str` (`.local` TLD) |
| Множественные записи журнала | `awaiting_departure` до съезда с весов |

### Осталось (limitations, не блокирует demo)

| # | Ограничение |
|---|-------------|
| 1 | RTSP camera — не реализован (`camera_core` только demo + http) |
| 2 | WebSocket `/ws/cameras/{id}` — отсутствует |
| 3 | Лимиты лицензии (`max_terminals` и др.) не enforced на create endpoints |
| 4 | owner-admin: нет UI модулей/offline issue/client users |
| 5 | installer: `service/`, `tray/` — только README-заглушки |
| 6 | DEMO terminal `stable_after=10s` — полный цикл ~12–14 с на весах |

---

## Статус

## `ACCEPTED_FOR_DEMO` (см. секцию Demo hardening pass)

MVP готов к уверенной демонстрации. Production-ограничения — в секции hardening и runbook.

---

## 3 следующих действия (post-MVP)

1. **Enforce license limits** — проверять `max_terminals` / `max_cameras` / `max_workplaces` в POST endpoints local-api.
2. **RTSP camera provider** — реализовать stub с reconnect или полноценный провайдер; добавить `/ws/cameras/{id}`.
3. **owner-admin UX** — экраны модулей, offline issue, seed demo user `owner@demo.local`.

---

## Demo hardening pass

**Дата:** 2026-06-29 (после приёмки)

### Исправлено

| Область | Изменение |
|---------|-----------|
| Bootstrap | Preflight PG/php/composer; auto `composer install`; синхронизация DB user и ключей |
| Demo terminal | Быстрый цикл (ramp 3s, stable 4s); `signal_departure()` — съезд с весов без дублей журнала |
| Журнал | Duplicate protection по окну; одна запись на цикл |
| UI panel | Русские статусы (журнал, лицензия, dashboard, FSM live) |
| API cameras | Порядок маршрутов: `/alpr/test` до `/{camera_id}/test` |
| Smoke | `./scripts/demo-smoke.sh` (+ `DEMO_SMOKE_FULL=1`) |
| Документация | `docs/08-demo-runbook.md` |

### Команды

```bash
./scripts/dev-bootstrap.sh
# запустить 3 сервиса (см. docs/08-demo-runbook.md)
./scripts/demo-smoke.sh
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

### Тесты

**20 passed**, 1 skipped. Smoke: `./scripts/demo-smoke.sh` и `DEMO_SMOKE_FULL=1` — PASS.

### Ограничения (остались, production-only)

- RTSP / WS cameras
- License limits enforcement
- owner-admin полный UI
- Windows installer

### Статус после hardening

## `ACCEPTED_FOR_DEMO`

Demo-сценарий стабилен: bootstrap → smoke → login → Demo Lane → журнал за ~8 с, без дублей при повторном цикле после съезда.
