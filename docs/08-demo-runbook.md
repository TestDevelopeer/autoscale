# 08 — Demo Runbook

Краткая инструкция для демонстрации Autoscale MVP.

---

## Требования

- PostgreSQL 17 на `127.0.0.1:5432`
- Python 3.12+, PHP 8.4+, Composer
- Порты свободны: **8000**, **8081**, **8090**

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
cd apps/local-panel && php artisan serve --host=127.0.0.1 --port=8081

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
| Панель (вход) | http://127.0.0.1:8081/login |
| Панель (admin) | http://127.0.0.1:8081/admin |
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

---

## Windows PowerShell quick start

Требования те же: PostgreSQL 17, Python 3.11+, PHP 8.4+, Composer. Порты **8000**, **8081**, **8090** свободны.

### 1. Bootstrap (один раз)

```powershell
$env:PGUSER = "postgres"
$env:PGHOST = "127.0.0.1"
$env:PGPORT = "5432"
$env:PGPASSWORD = "your-password"   # local session only, do not commit

.\scripts\dev-bootstrap.ps1
.\scripts\start-demo.ps1
.\scripts\demo-smoke.ps1
.\scripts\demo-smoke.ps1 -Full
```

Опциональные переменные: `LOCAL_DB_NAME` (по умолчанию `autoscale_local`), `OWNER_DB_NAME` (по умолчанию `autoscale_owner`).

### 2. Запуск demo

```powershell
.\scripts\start-demo.ps1
```

Сервисы стартуют в фоне; логи: `storage\logs\demo\`.

### 3. Smoke-проверка

```powershell
.\scripts\demo-smoke.ps1
.\scripts\demo-smoke.ps1 -Full
```

### 4. Панель оператора

| URL | http://127.0.0.1:8081/login |
| Логин | `operator@demo.local` / `demo` |

### 5. Остановка demo

```powershell
.\scripts\stop-demo.ps1
```

### 6. Health (PowerShell / cmd)

```powershell
curl.exe -i http://127.0.0.1:8000/api/health
```

Ожидание: `HTTP/1.1 200 OK`, `"status":"ok"`.

### Примечания

- Используйте **PowerShell**, не WSL bash — `dev-bootstrap.sh` для Linux/macOS/Git Bash.
- Shell-скрипты (`.sh`) в репозитории с LF; при ошибке `pipefail: invalid option name` выполните `git checkout -- scripts/*.sh`.
- На Windows venv: `.venv\Scripts\python.exe` (создаётся bootstrap-скриптом).
