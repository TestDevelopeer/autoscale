# 05 — Драйверы оборудования

## Общие интерфейсы

Расположение: `packages/hardware-core/`

### TerminalDriver

```python
class TerminalDriver(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def test_connection(self) -> TestResult: ...
    def read_frame(self) -> bytes | str: ...
    def parse_frame(self, raw: bytes | str) -> TerminalReading: ...
    def get_current_weight(self) -> TerminalReading: ...
    def get_status(self) -> TerminalStatus: ...
    def zero(self) -> bool: ...  # если поддерживается
    def health(self) -> HealthReport: ...
    def capabilities(self) -> TerminalCapabilities: ...
```

### TerminalReading

| Поле | Тип | Описание |
|------|-----|----------|
| `weight` | Decimal | Значение |
| `unit` | str | kg, t |
| `stable` | bool | Флаг стабильности |
| `raw` | str | Сырой ответ |
| `timestamp` | datetime | UTC |
| `status` | str | ok / error / timeout |
| `error` | str \| null | Текст ошибки |
| `protocol` | str | keli_modbus / cas_stream / demo |
| `metadata` | dict | Доп. поля |

### CameraProvider

```python
class CameraProvider(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def get_snapshot(self) -> bytes: ...
    def get_stream_status(self) -> StreamStatus: ...
    def health(self) -> HealthReport: ...
    def reconnect(self) -> None: ...
```

### ALPRProvider

```python
class ALPRProvider(Protocol):
    def recognize(self, image: bytes, roi: RoiRect | None = None) -> list[PlateCandidate]: ...
```

### PlateCandidate

| Поле | Тип |
|------|-----|
| `plate_raw` | str |
| `plate_normalized` | str |
| `confidence` | float 0..1 |
| `region` | bbox \| null |
| `timestamp` | datetime |
| `provider` | str |
| `metadata` | dict |

---

## Нормализация российских номеров

`packages/alpr-core/normalization.py`:

1. Uppercase.
2. Убрать пробелы, дефисы.
3. Homoglyphs кириллица ↔ латиница:

| Latin | Cyrillic |
|-------|----------|
| A | А |
| B | В |
| E | Е |
| K | К |
| M | М |
| H | Н |
| O | О |
| P | Р |
| C | С |
| T | Т |
| X | Х |
| Y | У |

4. Хранить `plate_raw` (как распознано) и `plate_normalized` (для поиска) отдельно.
5. Валидация формата RU (опционально warning, не block в MVP).

---

## Терминал: Keli D2008FA

**Пакет:** `packages/terminal-drivers/keli_d2008fa/`

### Конфигурация

| Параметр | Default | Описание |
|----------|---------|----------|
| `port` | COM3 | COM-порт |
| `baudrate` | 9600 | |
| `parity` | N | N/E/O |
| `stop_bits` | 1 | |
| `data_bits` | 8 | |
| `timeout_ms` | 1000 | |
| `device_id` | 1 | Modbus slave ID |
| `mode` | modbus_poll | modbus_poll / passive_stream (TODO) |
| `reconnect_policy` | exponential | |

### Протокол MVP

**Основной режим: Modbus RTU polling** (по результатам asp-autoscale HW-тестов).

- Function `0x03` Read Holding Registers.
- Парсер извлекает ASCII-фрагмент веса и флаг stable из response frame.
- Polling interval: 100–200 ms.

**Passive stream (TF=7):** зарезервирован; на тестовом железе не дал данных. TODO после верификации с `docs/18-keli_d2008f_guide.pdf`.

### Референс

- asp-autoscale: `src/api/terminals/keli_d2008f/`
- Руководство: asp-autoscale `docs/18-keli_d2008f_guide.pdf`

### Unit tests

Фикстуры raw Modbus frames → expected `TerminalReading`. Без реального COM в CI.

### TODO (после теста на железе)

- [ ] Подтвердить register map для D2008FA
- [ ] Проверить passive stream mode
- [ ] Уточнить unit (kg vs t) из регистра
- [ ] `zero()` — поддерживаемая команда?

---

## Терминал: CAS CI-200A

**Пакет:** `packages/terminal-drivers/cas_ci200a/`

### Конфигурация

| Параметр | Default |
|----------|---------|
| `port` | COM1 |
| `baudrate` | 19200 |
| `parity` | N |
| `stop_bits` | 1 |
| `data_bits` | 8 |
| `protocol_mode` | stream |
| `device_id` | 0 |
| `timeout_ms` | 2000 |

### Протокол MVP

1. **Stream mode** — непрерывные кадры (CAS 22 byte и аналоги).
2. **Command mode fallback** — при timeout stream: команда `WT`, парсинг response.
3. Parser: `packages/terminal-drivers/cas_ci200a/parser.py`

### Референс

- asp-autoscale: `src/api/terminals/ci200/`
- Руководство: asp-autoscale `docs/17-cas_ci200_guide.pdf`

### Особенности

- `device_id=0` — отдельная ветка serialization (из asp-autoscale fix HW10).
- `test_connection()`: stream probe → command probe → aggregate result.

### Unit tests

Примеры кадров из документации и зафиксированных логов asp-autoscale.

### TODO (после теста на железе)

- [ ] Полный набор command-mode команд (zero, tare)
- [ ] Верификация 22-byte frame layout на CI-200A
- [ ] Baudrate auto-detect (optional)

---

## Терминал: DEMO

**Пакет:** `packages/terminal-drivers/demo/`

Синтетический драйвер для разработки и demo:

- Фазы: idle (0) → ramp → stable plateau → optional drop.
- Configurable `target_weight`, `ramp_seconds`, `stable_after`.
- `stable` flag синхронизирован с фазой.
- `raw` — человекочитаемый debug string.

Полностью работает в MVP без железа.

---

## Камеры

**Пакет:** `packages/camera-core/`

| Provider | Подключение | MVP |
|----------|-------------|-----|
| `RtspCameraProvider` | RTSP URL | OpenCV / ffmpeg backend |
| `HttpSnapshotProvider` | HTTP GET image URL | Basic auth optional |
| `UsbCameraProvider` | Local index | Best-effort; platform-dependent |
| `DemoCameraProvider` | Loop mp4 / static jpg | Полный MVP |

### Общие настройки

| Поле | Описание |
|------|----------|
| `connection_type` | rtsp / http / usb / demo |
| `url` | RTSP or HTTP URL |
| `username` / `password` | Encrypted in DB |
| `roi` | JSON rect для ALPR |
| `reconnect_after_failures` | int |
| `reconnect_after_stale_seconds` | float |
| `rtsp_open_timeout_ms` | int |
| `rtsp_read_timeout_ms` | int |

### Reconnect

Exponential backoff; status: `connecting`, `running`, `degraded`, `error`.

---

## ALPR providers

**Пакет:** `packages/alpr-core/`

| Provider | Назначение | MVP |
|----------|------------|-----|
| `DemoAlprProvider` | Фиксированные номера по таймеру | Default |
| `MockAlprProvider` | Настраиваемый ответ для tests | Tests |
| `NomeroffNetProvider` | Production RU offline | Opt-in |

### NomeroffNetProvider — установка (production)

```bash
pip install nomeroff-net  # extra: alpr-nomeroff
# Скачать модели согласно README nomeroff-net
```

Требования: Python 3.9+, PyTorch (CPU/GPU), ~2GB models.

Документация: https://github.com/ria-com/nomeroff-net

### Лицензирование ALPR

Модуль `alpr` в license file обязателен для автоматического распознавания. Без него:

- Камера работает (preview, snapshot).
- `ALPRProvider` не вызывается; ручной ввод номера доступен.

---

## Health и diagnostics

Каждый driver реализует `health()`:

```python
@dataclass
class HealthReport:
    status: Literal["ok", "degraded", "error"]
    message: str
    last_success_at: datetime | None
    last_error: str | None
    metrics: dict
```

Агрегация в `GET /api/health` и `/ws/health`.

---

## Тестирование без железа

| Компонент | Подход |
|-----------|--------|
| Keli/CAS parsers | Unit tests на fixture frames |
| DEMO terminal | Integration + demo scenario |
| DEMO camera | Loop video in dev |
| FSM | Mock drivers |
| COM port | Не в CI; manual HW checklist в docs/06 |

---

## Матрица готовности

| Driver | Parser tests | DEMO | HW verified |
|--------|-------------|------|-------------|
| Keli D2008FA | Planned Phase 4 | N/A | TODO |
| CAS CI-200A | Planned Phase 4 | N/A | TODO |
| DEMO terminal | Phase 4 | Yes | N/A |
| RTSP camera | Phase 4 | Partial | TODO |
| HTTP camera | Phase 4 | Yes | TODO |
| DemoAlpr | Phase 4 | Yes | N/A |
| NomeroffNet | Documented | Opt-in | TODO |
