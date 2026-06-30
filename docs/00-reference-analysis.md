# 00 — Анализ референсов

Документ фиксирует, что взято из референсных продуктов, какие решения сохраняем в новом MVP и что намеренно не переносим.

## Референсы

| Референс | Назначение | Ссылка |
|----------|------------|--------|
| asp-autoscale | Архитектура локального runtime, лицензирование, терминалы, камеры, installer | https://github.com/TestDevelopeer/asp-autoscale |
| UniServer AUTO | Продуктовая модель модульных плагинов и orchestration автовесов | https://docuwiki.vesysoft.ru/doku.php?id=webapi:uniserver_auto |

---

## asp-autoscale — что переносим

| Область | Решение в референсе | Решение в MVP | Примечание |
|---------|---------------------|---------------|------------|
| Runtime boundary | FastAPI как единый hardware/runtime слой | `apps/local-api` (FastAPI) | Сохраняем server-first подход |
| Локальная панель | Laravel + Orchid за runtime | `apps/local-panel` (Orchid, stateless) | UI не работает с железом напрямую |
| Внешняя админка | Отдельный Laravel + Orchid для лицензий | `apps/owner-admin` | Изоляция владельца продукта |
| Лицензирование | Ed25519, offline `license.lic`, machine fingerprint | `packages/license-core` | Модульные features, не жёсткие тарифы |
| Терминалы | Keli D2008F, CAS CI-200, DEMO, session + WS frames | `packages/terminal-drivers` | Парсеры и протоколы — референс, код пишем заново |
| Камеры | Единый CameraRuntimeSupervisor, один ingest → preview + ALPR | `packages/camera-core` | Один supervisor на камеру |
| Realtime | REST + WebSocket для веса, камер, health | `/ws/*` в local-api | Панель подписывается на WS напрямую |
| Health / диагностика | `/api/health`, support bundle, логи | Раздел «Настройки / Диагностика» | Без fleet-telemetry |
| Installer | Windows Service, tray, Inno Setup skeleton | `installer/` | MVP — skeleton, не production installer |
| DEMO-режим | Synthetic terminal/camera для разработки | Обязателен в MVP | Demo Lane в seed |

## asp-autoscale — что не переносим

| Область | Почему не переносим |
|---------|---------------------|
| FastAPI запускает Laravel stack | Усложняет отладку; в MVP — отдельные процессы (docker-compose / installer) |
| Laravel владеет operational DB | В MVP единственный владелец БД — `local-api` |
| Per-user license token + WS binding | Избыточно для MVP; лицензия на уровне installation |
| Fleet / heartbeat / runtime nodes | Вне scope MVP |
| Release/update pipeline v1–v4 | Вне scope MVP |
| 200+ инкрементальных docs | Заменяем структурированными docs/00–06 |
| Legacy desktop UI | Основной клиент — web-панель на localhost |
| Fast-ALPR (ONNX) как единственный ALPR | Для RU-номеров выбираем nomeroff-net; fast-alpr не переносим |
| Integrity telemetry / security events queue | Упрощаем до audit_log + support bundle |

---

## UniServer AUTO — что переносим

| Область | Решение в UniServer | Решение в MVP |
|---------|---------------------|---------------|
| Модульная архитектура | Плагины: WeightIndicator, Camera, Recognize, Journal, AutoScale | Независимые adapters + orchestration |
| Orchestration | Core.CommandMap / AutoScale plugin | `WorkplaceOrchestrator` в local-api |
| Весовой индикатор | RS-232, Massa, Stabil, Parameters | `TerminalDriver` + WebSocket live |
| Камера | RTSP/HTTP, GetFrameJpg | `CameraProvider.get_snapshot()` |
| Распознавание | Recognize plugin | `ALPRProvider` (модуль лицензии `alpr`) |
| Журнал | Journal plugin | `weighing_records` + UI журнала |
| AutoScale state | StateName, Stabil, modeAuto, WeighingResult | Explicit FSM (см. docs/04-weighing-workflow.md) |
| Рабочее место | Сборка терминала + камер + настроек | `workplaces` entity |
| Авто/ручной режим | SetAutoMode, Enable | `auto_confirm` / `manual_confirm` на workplace |

## UniServer AUTO — что не переносим

| Область | Почему |
|---------|--------|
| RFID / UHF (ScanRFID) | Вне MVP |
| УДВВ, светофоры, шлагбаумы | Вне MVP |
| LED-панели (LedPanel) | Вне MVP |
| Двукратное взвешивание / нетто-режимы | Вне MVP (только фиксация брутто) |
| FastReport / печать документов | Вне MVP |
| Вагонные / поосные весы | Вне MVP |
| 1С интеграция | Вне MVP |
| CommandMap как публичный HTTP API | Заменяем REST + OpenAPI |

---

## Уроки с реального железа (asp-autoscale)

Эти наблюдения влияют на дизайн драйверов в docs/05-hardware-drivers.md.

### Keli D2008FA

- Настройка **TF=7** (пассивный ASCII-поток) на практике может не давать непрерывных кадров: passive listen на COM возвращал 0 байт.
- Рабочий режим на том же оборудовании — **Modbus RTU polling** (TF=1 style): `9600 8N1`, `device_id=1`, function `0x03`.
- **Вывод для MVP:** основной путь драйвера — Modbus polling; passive stream — опциональный режим с TODO после проверки на железе.

### CAS CI-200A

- Stream-режим может таймаутиться; **command-mode fallback** (`WT` и др.) даёт успешный test connection.
- Device ID = 0 требует отдельной обработки в command serialization.
- **Вывод для MVP:** `test_connection()` пробует stream, затем command-mode; parser unit tests на зафиксированных кадрах.

### Камеры

- RTSP требует явных timeout/reconnect policy.
- Единый ingest loop для preview и ALPR снижает нагрузку на камеру.
- DEV: loop mp4 как источник вместо RTSP.

---

## Принцип чистого MVP

Новый продукт **не копирует** код asp-autoscale слепо. Переносим:

1. Проверенные **архитектурные границы** (runtime / panel / owner-admin).
2. **Интерфейсы** оборудования и лицензий.
3. **Протокольные знания** (парсеры, режимы Keli/CAS) как референс для unit tests.
4. **Продуктовую модель** UniServer (модули + orchestration).

Переписываем с нуля: структура монорепо, FSM взвешивания, api-only DB, OpenAPI-контракты, Orchid screens как thin API clients.
