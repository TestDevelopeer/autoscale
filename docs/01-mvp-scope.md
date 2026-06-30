# 01 — Границы MVP

Документ фиксирует, что входит и не входит в первую итерацию продукта автоматизации взвешивания на автомобильных весах.

## Цель MVP

Автоматизировать сценарий: автомобиль заезжает → камера распознаёт госномер РФ → вес стабилизируется → система фиксирует взвешивание в журнале с привязкой к карточке водителя/ТС (или предлагает создать карточку).

Основной клиент — **локальная web-панель** (`http://127.0.0.1:8080`), не desktop UI.

---

## Входит в MVP

### Приложения

| Компонент | Описание |
|-----------|----------|
| `apps/owner-admin` | Внешняя панель владельца: клиенты, пользователи, лицензии, модули, offline issue |
| `apps/local-api` | Локальный runtime: оборудование, workflow, WebSocket, health, лицензии, БД, auth |
| `apps/local-panel` | Локальная панель оператора (Orchid), stateless, общается только с local-api |
| `packages/*` | license-core, hardware-core, terminal-drivers, camera-core, alpr-core, shared-contracts |
| `installer/` | Skeleton: Windows Service, tray, команды запуска/перезапуска |

### Лицензирование

- Модульные features (не basic/pro/full)
- Online activation и offline license file (Ed25519)
- Machine fingerprint, anti-rollback, grace period
- Feature gating в local-api и UI

Минимальные модули: `core`, `terminals`, `cameras`, `alpr`, `weighing_journal`, `drivers_registry`, `workplaces`, `reports_basic`, `api_access`, `multi_workplace`.

### Оборудование

| Тип | Поддержка MVP |
|-----|---------------|
| Терминалы | Keli D2008FA, CAS CI-200A, DEMO |
| Камеры | RTSP, HTTP snapshot, DEMO (loop video/image) |
| ALPR | Provider interface + Demo/Mock; nomeroff-net — opt-in production path |

### Функциональность панели

1. **Dashboard** — статус лицензии, API, БД, терминалов, камер, ALPR, рабочих мест
2. **Оборудование** — терминалы и камеры (CRUD, test, live preview)
3. **Рабочие места** — сборка терминала + камер, live workflow, ручные действия
4. **Журнал взвешивания** — таблица записей, детализация, привязка водителя, отмена
5. **Водители / Автомобили** — карточки, поиск по нормализованному номеру
6. **Лицензия** — статус, activation, import/export файлов
7. **Настройки / Диагностика** — health, логи, support bundle, версия

### Workflow

- Explicit state machine (см. docs/04-weighing-workflow.md)
- Duplicate protection window
- Auto и manual confirm
- Сохранение: номер, вес, стабильность, снимки, raw terminal frame, operator

### API

- REST endpoints из ТЗ
- WebSocket: health, terminals, cameras, workplaces
- OpenAPI в `packages/shared-contracts`

### Качество

- Unit tests: terminal parsers, FSM, license verification
- Feature tests: Orchid screens (ключевые flows)
- Demo mode без реального железа
- Seed/demo данные
- Docker-compose для dev

---

## Не входит в MVP

| Область | Комментарий |
|---------|-------------|
| 1С интеграция | Post-MVP |
| Оплата / биллинг | Post-MVP |
| RFID / UHF метки | Post-MVP |
| Шлагбаумы, светофоры, УДВВ | Post-MVP |
| LED табло | Post-MVP |
| Сложные отчёты | Только `reports_basic` module flag; UI минимален |
| Экспорт CSV/XLSX журнала | Заложить в API/UI stub; полная реализация опциональна |
| Облачное хранение видео | Локальные snapshots only |
| Мобильное приложение | Post-MVP |
| Мультифилиальная аналитика | Post-MVP |
| Fleet monitoring / heartbeat nodes | Post-MVP |
| Production auto-updater | Skeleton only |
| Production Windows installer (Inno Setup полный цикл) | Skeleton + dev scripts |
| Двукратное взвешивание / расчёт нетто | Post-MVP |
| Desktop UI как основной интерфейс | Только thin tray для запуска |
| Облачное ALPR | Только offline providers |

---

## Demo mode

Для демонстрации без терминала и камеры:

| Компонент | Поведение |
|-----------|-----------|
| DEMO terminal | Синтетическая кривая веса с флагом stable |
| DEMO camera | Loop тестового mp4 или статичный кадр |
| DemoAlprProvider | Возвращает предустановленные номера с confidence |
| Seed workplace | «Demo Lane» — готовое рабочее место |
| Demo credentials | `operator@demo.local` / `demo` |

---

## Критерий «MVP готов»

См. полный checklist в [docs/06-acceptance.md](06-acceptance.md).

Кратко:

1. Owner-admin создаёт лицензию и выдаёт offline/online activation.
2. Local-api активирует лицензию, блокирует модули без entitlement.
3. Оператор настраивает DEMO terminal + camera + workplace.
4. Workflow проходит от IDLE до COMPLETED в demo mode.
5. Запись появляется в журнале с номером, весом, снимком.
6. Карточка водителя создаётся из записи без существующего номера.
7. Health и support bundle доступны.

---

## Фазы реализации

| Фаза | Содержание |
|------|------------|
| 0 | Документация (этот набор docs) |
| 1 | Skeleton: монорепо, docker, health |
| 2 | License core + owner-admin |
| 3 | Local-api auth + panel license gating |
| 4 | Equipment: terminals, cameras, ALPR, WS |
| 5 | Workplaces + weighing FSM + journal |
| 6 | Drivers/vehicles registry |
| 7 | Acceptance tests + demo scenario |
