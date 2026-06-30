# 09 — Production Roadmap (после MVP)

Документ описывает следующий этап развития Autoscale **без реализации**. Текущая стабильная точка: **ACCEPTED_FOR_DEMO** (см. [`10-demo-freeze.md`](10-demo-freeze.md)).

---

## Цель production-этапа

Вывести Autoscale с синтетического demo на **один реальный объект** (пилот): стабильное взвешивание с реальными весами и камерой, управляемая лицензия, установка под Windows, минимальная эксплуатация без разработчика рядом.

---

## Что уже готово в MVP

| Область | Состояние |
|---------|-----------|
| Монорепо | apps (local-api, local-panel, owner-admin) + packages + installer skeleton |
| Runtime | FastAPI, FSM workplace, журнал, WebSocket terminal/workplace |
| Лицензии | Ed25519, PHP/Python canonical JSON, feature-gating на API, demo license в seed |
| UI | Orchid panel: dashboard, equipment, workplaces, journal, license, diagnostics |
| Demo | DEMO terminal/camera/ALPR, bootstrap + smoke-скрипты |
| Тесты | 20 passed, 1 skipped; защита demo-flow |
| Документация | docs/00–08, acceptance report, demo freeze |

---

## Что нельзя ломать

- **Demo-flow:** bootstrap → login → Demo Lane → start → запись A123BC77 / ~15000 kg
- **Smoke:** `./scripts/demo-smoke.sh`, `DEMO_SMOKE_FULL=1 ./scripts/demo-smoke.sh`
- **Лицензирование:** canonical JSON, cross-sign PHP↔Python, `require_module()` на роутерах
- **Архитектура:** local-api владеет БД и auth; panel stateless через API token
- **Bootstrap без Docker:** PostgreSQL 17, `scripts/dev-bootstrap.sh`
- **Учётные данные demo:** `operator@demo.local` / `demo`

Любое изменение в перечисленном — только с обновлением smoke-тестов и `docs/10-demo-freeze.md`.

---

## Production-only ограничения (из acceptance report)

| # | Ограничение | Влияние на demo |
|---|-------------|-----------------|
| 1 | RTSP camera не реализован | Нет — demo использует DEMO camera |
| 2 | WebSocket `/ws/cameras/{id}` отсутствует | Нет |
| 3 | License limits не enforced на create API | Нет для demo |
| 4 | owner-admin: неполный UI (модули, offline, users) | Нет для operator demo |
| 5 | installer: только scripts + README-заглушки | Нет |
| 6 | Нет 1С, RFID, шлагбаумов, биллинга, fleet | Нет |

---

## Этап 1: Проверка реального железа Keli D2008FA и CAS CI-200A

**Статус:** в работе (`feature/hardware-validation`)

**Документ:** [`11-hardware-validation-plan.md`](11-hardware-validation-plan.md)

**Цель:** подтвердить парсеры и polling/stream на реальных весах.

**Работы:**
- Подключение по Modbus (Keli) и serial/stream (CAS)
- Карта регистров / формат кадров на объекте
- Стабильность флага `stable`, единицы (kg/t)
- Интеграционные тесты с записанными raw-кадрами
- Документация отклонений от `docs/05-hardware-drivers.md`

**Критерий выхода:** 30+ мин непрерывного чтения без потери связи; вес на panel совпадает с индикатором весов.

---

## Этап 2: RTSP/WS камеры и стабильный camera runtime

**Цель:** live snapshot и reconnect для production-камер.

**Работы:**
- RTSP provider в `camera_core`
- Reconnect, timeout, health
- WebSocket `/ws/cameras/{id}` (preview frames / snapshot events)
- ROI в ALPR pipeline

**Критерий выхода:** snapshot < 3 с после connect; автоматический reconnect после обрыва RTSP.

---

## Этап 3: Production ALPR для российских номеров

**Цель:** заменить DemoAlprProvider на реальное распознавание ГРЗ РФ.

**Работы:**
- Интеграция выбранного движка (например Nomeroff / custom)
- Нормализация кириллица/латиница (уже есть в `alpr-core`)
- Accuracy на фото с объекта
- Feature-gating модуля `alpr` без регрессии demo

**Критерий выхода:** ≥90% на тестовой выборке с полосы; demo ALPR остаётся для offline demo.

---

## Этап 4: License limits на API-уровне

**Цель:** лимиты из license file реально ограничивают создание сущностей.

**Работы:**
- `max_terminals`, `max_cameras`, `max_workplaces`, `max_users` в POST endpoints
- Понятные 403 с сообщением для UI
- Тесты на превышение лимита

**Критерий выхода:** нельзя создать N+1 terminal при лимите N; demo license не ломается.

---

## Этап 5: Полный owner-admin UI

**Цель:** выпуск и управление лицензиями без ручных SQL/JSON.

**Работы:**
- UI модулей и лимитов
- Offline activation request / issue
- Клиенты и пользователи
- Demo user `owner@demo.local` в seed

**Критерий выхода:** online/offline activation end-to-end через UI без правки файлов вручную.

---

## Этап 6: Windows installer + service + tray

**Цель:** установка на ПК объекта одним инсталлятором.

**Работы:**
- `installer/service/` — Windows Service для local-api
- `installer/tray/` — статус, open panel, restart
- Inno Setup (или аналог), PostgreSQL external
- Support bundle на production

**Критерий выхода:** чистая Windows VM: install → health OK → panel открывается.

---

## Этап 7: Пилот на одном объекте

**Цель:** эксплуатация на реальной полосе взвешивания.

**Работы:**
- Один workplace, реальный terminal + camera + ALPR
- Обучение оператора, runbook эксплуатации
- Сбор инцидентов 2–4 недели
- Решение go/no-go для тиражирования

**Критерий выхода:** см. «Минимальные критерии готовности к пилоту» ниже.

---

## Риски

| Риск | Митигация |
|------|-----------|
| Несовместимость протокола весов | Ранний этап 1 на объекте; fallback command-mode |
| RTSP нестабилен на площадке | Буфер snapshot, retry, диагностика в panel |
| ALPR ошибки на грязных номерах | Ручное подтверждение в journal; порог confidence |
| Регресс demo при доработках | Smoke перед merge; freeze-документ |
| Лицензия на другом ПК | Документированный offline flow |
| Bus factor installer | Этап 6 только после стабильного пилотного runtime |

---

## Минимальные критерии готовности к пилоту

1. Реальный terminal (Keli или CAS) — stable weight ≥ 1 смена
2. Камера — snapshot + ALPR на объекте
3. FSM end-to-end без зависаний (не только DEMO)
4. Журнал с корректными полями и статусами на русском
5. Лицензия active, limits enforced
6. Установка через installer или documented manual install < 2 ч
7. `./scripts/demo-smoke.sh` и pytest green на CI
8. Runbook эксплуатации для оператора и поддержки

---

## Рекомендуемый порядок

```text
Этап 1 (железо весов) → Этап 2 (камера) → Этап 3 (ALPR)
    → Этап 4 (limits) → Этап 5 (owner-admin UI)
    → Этап 6 (installer) → Этап 7 (пилот)
```

Параллельно допустимо: этап 4 + 5 после стабилизации 1–3.
