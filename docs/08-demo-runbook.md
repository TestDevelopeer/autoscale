# 08 — Demo Runbook

Краткая инструкция для демонстрации Autoscale MVP.

---

## Требования

- PostgreSQL 17 на `127.0.0.1:5432`
- Python 3.12+, PHP 8.4+, Composer
- Порты свободны: **8000**, **8080**, **8090**

---

## 1. Подготовка (один раз)

```bash
createdb autoscale_local   # если БД ещё нет
createdb autoscale_owner
chmod +x scripts/dev-bootstrap.sh scripts/demo-smoke.sh
./scripts/dev-bootstrap.sh
```

---

## 2. Запуск сервисов (3 терминала)

```bash
# Терминал 1 — API
cd apps/local-api && ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Терминал 2 — панель оператора
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8080

# Терминал 3 — owner-admin (опционально для demo лицензий)
cd apps/owner-admin && php artisan serve --host=127.0.0.1 --port=8090
```

---

## 3. Smoke-проверка

```bash
./scripts/demo-smoke.sh
```

Полный цикл с записью в журнале (~10 с):

```bash
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
```

---

## 4. URL и логин

| Сервис | URL |
|--------|-----|
| Панель (вход) | http://127.0.0.1:8080/login |
| Панель (admin) | http://127.0.0.1:8080/admin |
| API health | http://127.0.0.1:8000/api/health |
| owner-admin | http://127.0.0.1:8090 |

**Оператор:** `operator@demo.local` / `demo`

---

## 5. Demo-сценарий (~8 с)

1. Войти в панель → Dashboard (зелёная лицензия).
2. **Рабочие места** → открыть **Demo Lane**.
3. Нажать **Старт** — на экране: состояние FSM, вес, номер.
4. Через ~6–8 с открыть **Журнал взвешивания**.

**Ожидаемая запись:**

| Поле | Значение |
|------|----------|
| Номер | A123BC77 |
| Вес | ~15 000 кг |
| Стабильный | Да |
| Статус | Нужна карточка водителя |
| Рабочее место | Demo Lane |

---

## 6. Health

```bash
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool
```

---

## 7. Остановка

`Ctrl+C` в каждом терминале с `uvicorn` / `artisan serve`.

---

## 8. Сброс demo-данных

```bash
./scripts/dev-bootstrap.sh   # idempotent: migrate + seed, обновляет demo license
```

Очистить только журнал (PostgreSQL):

```bash
psql -d autoscale_local -c "DELETE FROM weighing_records;"
```

---

## 9. Ограничения (не для production)

- Только DEMO terminal/camera/ALPR (без RTSP и реального железа)
- Лимиты лицензии (`max_terminals` и др.) не enforced в API
- owner-admin: минимальный UI
- Windows installer — skeleton only

Подробнее: [`docs/07-mvp-acceptance-report.md`](07-mvp-acceptance-report.md)
