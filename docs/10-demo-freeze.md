# 10 — Demo Freeze

**Версия:** MVP demo freeze  
**Статус:** `ACCEPTED_FOR_DEMO`  
**Ветка:** `feature/mvp`  
**Дата фиксации:** 2026-06-30

Этот документ фиксирует стабильную demo-версию Autoscale. Изменения, ломающие перечисленное ниже, требуют обновления smoke-тестов и согласования.

---

## Статус

```text
ACCEPTED_FOR_DEMO
```

Demo проходит стабильно: bootstrap → smoke → login → Demo Lane → журнал.

---

## Команды запуска

### Подготовка (один раз или после сброса)

```bash
createdb autoscale_local   # если БД нет
createdb autoscale_owner
chmod +x scripts/dev-bootstrap.sh scripts/demo-smoke.sh
./scripts/dev-bootstrap.sh
```

### Сервисы (3 терминала)

```bash
cd apps/local-api && ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8080
cd apps/owner-admin && php artisan serve --host=127.0.0.1 --port=8090   # опционально
```

Подробнее: [`08-demo-runbook.md`](08-demo-runbook.md)

---

## Demo логин

| Поле | Значение |
|------|----------|
| URL | http://127.0.0.1:8080/login |
| Email | `operator@demo.local` |
| Password | `demo` |

---

## Ожидаемый результат demo

1. Dashboard — local-api OK, лицензия «Активна»
2. **Рабочие места** → **Demo Lane** → **Старт**
3. Через ~6–8 с — **Журнал взвешивания**

| Поле | Ожидание |
|------|----------|
| Номер | `A123BC77` |
| Вес | ~15 000 кг |
| Стабильный | Да |
| Статус | Нужна карточка водителя |
| Рабочее место | Demo Lane |

---

## Тесты

```bash
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

**Зафиксированный результат:** `20 passed, 1 skipped`

Skipped: `test_license_php_python_compatible` (если PHP vendor недоступен в окружении; вручную canonical JSON совпадает).

---

## Smoke перед merge / показом

Сервисы должны быть запущены (как минимум local-api; для полного smoke — panel и owner-admin).

```bash
./scripts/demo-smoke.sh
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
```

Оба скрипта должны завершаться с **exit 0**.

| Скрипт | Что проверяет |
|--------|----------------|
| `demo-smoke.sh` | health, license, panel, owner-admin, DEMO equipment, journal endpoint |
| `DEMO_SMOKE_FULL=1` | + полный цикл start workplace → запись в журнале |

---

## Production-only ограничения

Не являются дефектами demo-версии:

- RTSP camera и `/ws/cameras/{id}` — не реализованы
- License limits (`max_terminals` и др.) — не enforced на POST API
- owner-admin — минимальный UI (нет полного управления модулями/offline)
- installer — только `scripts/` и README-заглушки `service/`, `tray/`
- Нет 1С, RFID, шлагбаумов, биллинга, fleet, production auto-updater

Следующий этап: [`09-production-roadmap.md`](09-production-roadmap.md)

---

## Что запрещено ломать в следующих ветках

| Компонент | Контракт |
|-----------|----------|
| `scripts/dev-bootstrap.sh` | Idempotent bootstrap на PG 17 без Docker |
| `scripts/demo-smoke.sh` | Exit 0 на frozen demo |
| Demo seed | `operator@demo.local`, DEMO Terminal/Camera, Demo Lane |
| Demo terminal | ~15000 kg, stable, `signal_departure()` без дублей журнала |
| Demo ALPR | `A123BC77` на `/api/cameras/alpr/test` |
| FSM loop | `start_workplace_loop` → journal record |
| License | PHP `LicenseCanonicalJson` ↔ Python `license_core.canonical` |
| Auth login | `operator@demo.local` / `demo` |
| Panel permissions | `platform.autoscale` при login |

При изменении любого пункта — обновить тесты, smoke и этот документ.

---

## Связанные документы

| Документ | Назначение |
|----------|------------|
| [`07-mvp-acceptance-report.md`](07-mvp-acceptance-report.md) | Отчёт приёмки и hardening |
| [`08-demo-runbook.md`](08-demo-runbook.md) | Пошаговый demo для оператора |
| [`09-production-roadmap.md`](09-production-roadmap.md) | Roadmap после MVP |
