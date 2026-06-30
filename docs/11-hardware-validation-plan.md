# 11 — Hardware Validation Plan (Этап 1)

**Ветка:** `feature/hardware-validation`  
**Статус demo:** `ACCEPTED_FOR_DEMO` — не ломать  
**Цель:** подготовить проверку реальных терминалов Keli D2008FA и CAS CI-200A без записей в журнале и без изменения DEMO flow.

---

## Цель проверки

1. Подтвердить чтение веса с реального COM-порта.
2. Зафиксировать raw frames и результат парсера.
3. Выявить корректные настройки порта (baudrate, parity, device_id).
4. Подготовить данные для уточнения register map (Keli) и frame layout (CAS).
5. Не затрагивать FSM, журнал и demo-сценарий.

---

## Поддерживаемые терминалы

| Терминал | driver type | Протокол MVP | Default baud | Default parity |
|----------|-------------|--------------|--------------|----------------|
| Keli D2008FA | `keli_d2008fa` / `keli-d2008fa` | ASCII continuous stream (+ Modbus poll fallback) | 9600 | **none (N)** — проверено на объекте; even давал битый raw |
| CAS CI-200A | `cas_ci200a` / `cas-ci-200a` | stream + fallback `WT` | 19200 | none (N) |
| DEMO | `demo` | синтетика | — | — |

---

## Параметры COM для проверки

| Параметр | Keli (старт) | CAS (старт) | Примечание |
|----------|--------------|-------------|------------|
| port | COM3 / `/dev/ttyUSB0` | COM1 / `/dev/ttyUSB0` | **не хардкодить** — задавать явно |
| baudrate | 9600 | 19200 | при ошибках пробовать 4800/19200 |
| parity | **none (N)** — проверено на COM1 | none (N) | mismatch → мусор в raw; Keli: even → `parse_failed` |
| data_bits | 8 | 8 | |
| stop_bits | 1 | 1 | |
| timeout | 2 s | 2 s | увеличить при медленном ответе |
| device_id | 1 | 0 | Keli Modbus slave; CAS command mode |

---

## Подключение Keli D2008FA

1. Подключить RS-232/USB-адаптер к терминалу и ПК.
2. В диспетчере устройств определить имя порта (например `COM5`).
3. Убедиться, что порт не занят другой программой.
4. Запустить probe (без local-api journal):

```bash
python apps/local-api/scripts/terminal_probe.py \
  --driver keli-d2008fa \
  --port COM5 \
  --baudrate 9600 \
  --parity even \
  --device-id 1 \
  --timeout 2 \
  --duration 30 \
  --out storage/probes/keli-com5.json
```

5. На весах поставить груз или дождаться стабильного веса.
6. Сохранить JSON-отчёт и raw samples.

**Ожидание:** `success_count > 0`, в `parsed_samples` — вес > 0, при стабилизации `stable=true`.

---

## Подключение CAS CI-200A

```bash
python apps/local-api/scripts/terminal_probe.py \
  --driver cas-ci-200a \
  --port COM5 \
  --baudrate 19200 \
  --parity none \
  --timeout 2 \
  --duration 30 \
  --out storage/probes/cas-com5.json
```

Probe сначала читает stream; при пустом буфере отправляет `WT\r\n`.

---

## Что зафиксировать при тесте

| Данные | Где |
|--------|-----|
| Имя порта, baud, parity | `port_settings` в JSON |
| Raw frames (hex + ascii) | `raw_samples` |
| Parsed weight, stable, unit | `parsed_samples` |
| Ошибки и предупреждения | `errors`, `warnings` |
| Итог и рекомендация | `summary`, `recommended_next_action` |
| Фото/скрин индикатора весов | вне репо (для сверки) |

---

## Команды

### Parser self-test (без железа)

```bash
python apps/local-api/scripts/terminal_probe.py --driver keli-d2008fa --fixture
python apps/local-api/scripts/terminal_probe.py --driver cas-ci-200a --fixture
python apps/local-api/scripts/terminal_probe.py --driver demo --duration 3
```

### Hardware smoke (с COM)

```bash
chmod +x scripts/hardware-smoke.sh
TERMINAL_PROBE_DRIVER=keli-d2008fa TERMINAL_PROBE_PORT=COM5 ./scripts/hardware-smoke.sh
TERMINAL_PROBE_DRIVER=cas-ci-200a TERMINAL_PROBE_PORT=COM5 TERMINAL_PROBE_BAUDRATE=19200 ./scripts/hardware-smoke.sh
```

Без `TERMINAL_PROBE_PORT` скрипт завершится с понятным SKIP (не traceback).

### Demo regression (обязательно перед merge)

```bash
./scripts/demo-smoke.sh
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
.venv/bin/python -m pytest -q packages apps/local-api/tests
```

---

## Экраны panel (после успешного probe)

1. **Терминалы** — создать терминал с `driver_type=keli_d2008fa` или `cas_ci200a`, указать `port` в config.
2. **Тест подключения** — `POST /api/terminals/{id}/test`: для Keli открывает реальный COM; для DEMO — синтетический self-test.
3. **Рабочее место** — только после стабильного hardware probe; для demo использовать **Demo Lane** (DEMO).

**Не запускать** hardware workplace на первом тесте — только probe CLI.

---

## Логи

| Источник | Что смотреть |
|----------|--------------|
| `terminal_probe.py` stdout | connected, success/failure, last raw/parsed |
| `storage/probes/*.json` | полный отчёт |
| local-api uvicorn | только если тестируете через API test endpoint |
| PostgreSQL `weighing_records` | **не должно появляться** при probe |

---

## Признаки успеха

- `connected: true`
- `success_count >= 1`
- `parsed_samples[].weight` совпадает с индикатором весов (± допуск)
- `stable=true` при стабильном грузе
- Нет постоянных `terminal_silent` / `read_timeout`

---

## Признаки проблем parser

| Симптом | Вероятная причина |
|---------|------------------|
| `parse_failed` при непустом raw | Неверный layout кадра — нужен новый парсер |
| Вес есть, `stable=false` всегда | Неверный флаг ST в кадре |
| `success` но вес неверный | Неверный register / лишние цифры в regex |
| `terminal_silent` | Неверный baud/parity или кабель |
| `port_not_found` | Неверное имя COM |
| `port_access_denied` | Порт занят |

---

## Откат в DEMO режим

1. Не менять seed: **Demo Lane** + **DEMO Terminal** остаются по умолчанию.
2. Остановить hardware workplace если был запущен.
3. Проверить demo smoke:

```bash
./scripts/demo-smoke.sh
DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh
```

4. В panel использовать только Demo Lane для показа.

---

## Keli D2008FA real validation result

**Дата проверки:** 2026-06-30  
**Инструмент:** `terminal_probe.py` (без записей в журнал и без FSM)

Терминал Keli D2008FA **реально проверен** на объекте через `terminal_probe`.

### Рабочие настройки COM

| Параметр | Значение |
|----------|----------|
| port | COM1 |
| baudrate | 9600 |
| parity | **none** |
| timeout | 2 s |

**Важно:** при `parity even` в raw приходили битые символы и `parse_failed`. При `parity none` кадры читаются как читаемый ASCII.

### Команда probe

```bash
python apps/local-api/scripts/terminal_probe.py \
  --driver keli-d2008fa \
  --port COM1 \
  --baudrate 9600 \
  --parity none \
  --timeout 2 \
  --duration 30
```

### Фактический результат

```
driver: keli_d2008fa
connected: True
success: 120
failures: 0
last parsed: weight=0 stable=True unit=kg status=ok
last raw: ST,GS,+0000000kg
```

### Формат кадра (ASCII continuous)

Parser поддерживает формат:

```text
<stability>,<weight_type>,<signed_weight><unit>
```

| Поле | Значение | Пример |
|------|----------|--------|
| stability | `ST` = stable, `US` = unstable | `ST` |
| weight_type | `GS` = gross, `NT` = net | `GS` |
| signed_weight | знак `+`/`-` и цифры | `+0000000` |
| unit | `kg`, `g`, `t`, `lb` (минимум `kg`) | `kg` |

Пример raw frame: `ST,GS,+0000000kg` → **0 kg**, stable, gross.

### Тесты после исправления parser

```text
37 passed, 1 skipped
```

### Ограничения проверки

- Проверка выполнялась **без создания записей в журнале** (`weighing_records` не затрагивались).
- DEMO flow не менялся.

### Следующий шаг

1. ~~Подключить Keli в **local-panel**~~ — см. секцию ниже.
2. Проверить **workplace live** на реальной полосе (после стабильного panel test).

---

## Keli D2008FA local-panel validation

**Статус:** `terminal_probe` подтвердил реальный COM; **local-panel** `test_connection` для `keli_d2008fa` использует тот же serial-слой (`probe.serial_io`) и открывает физический порт.

### Настройки (проверено на объекте)

| Параметр | Значение |
|----------|----------|
| type | `keli_d2008fa` (Keli D2008FA) |
| port | COM1 |
| baudrate | 9600 |
| parity | none |
| timeout | 2 s |

### Перед UI-тестом

1. Закройте **PuTTY**, **terminal_probe** и любые программы, занимающие COM1 — иначе panel покажет `port_access_denied`, а не 500.
2. Войдите в panel: http://127.0.0.1:8081/login → `operator@demo.local` / `demo`.
3. Откройте **Терминалы → Добавить** (`/admin/terminals/create`).
4. Заполните поля и нажмите **Проверить подключение**.

### Ожидаемый Toast при успехе

```text
connected=true, weight=0, stable=true, unit=kg, raw=ST,GS,+0000000kg
```

(вес и raw — актуальные с терминала)

### Цепочка вызовов

```text
local-panel → POST /api/terminals → POST /api/terminals/{id}/test
  → KeliD2008faDriver.test_connection()
  → keli_d2008fa/serial_session.py (open_serial, read frame)
  → parse_keli_modbus_response (parser без изменений)
```

**DEMO terminal** (`driver_type=demo`) по-прежнему использует `DemoTerminalDriver` — demo-smoke не затрагивается.

### Ошибки (без HTTP 500)

| error_code | Причина |
|------------|---------|
| `port_not_found` | COM-порт не найден |
| `port_access_denied` | Порт занят (PuTTY, probe, другая программа) |
| `read_timeout` | Нет ответа за timeout |
| `parse_failed` | raw получен, parser не распознал кадр |

---

## Связанные документы

- [`05-hardware-drivers.md`](05-hardware-drivers.md) — интерфейсы и протоколы
- [`09-production-roadmap.md`](09-production-roadmap.md) — этап 1 roadmap
- [`10-demo-freeze.md`](10-demo-freeze.md) — что нельзя ломать
