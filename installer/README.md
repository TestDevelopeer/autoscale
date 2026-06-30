# Windows installer / runtime skeleton

## Компоненты (MVP)

| Путь | Статус |
|------|--------|
| `scripts/` | PowerShell утилиты (open-panel, restart-api, support-bundle) |
| `service/` | **Заглушка** — план Windows Service wrapper для local-api |
| `tray/` | **Заглушка** — план tray app (статус, open panel, restart) |

## Команды (dev)

```powershell
.\scripts\open-panel.ps1
.\scripts\restart-api.ps1
.\scripts\support-bundle.ps1
```

## Production path (post-MVP)

- Inno Setup spec для единого установщика
- Установка PostgreSQL external
- Регистрация Windows Service (`service/`)
- Tray autostart (`tray/`)
