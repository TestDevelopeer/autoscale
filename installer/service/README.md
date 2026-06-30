# Windows Service wrapper (post-MVP)

Планируется:

- NSSM или pywin32 service для `uvicorn app.main:app`
- Автозапуск при старте Windows
- Логи в `%ProgramData%\Autoscale\logs`

MVP: запуск вручную или через `installer/scripts/restart-api.ps1`.
