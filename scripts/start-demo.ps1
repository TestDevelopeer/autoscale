# Start Autoscale demo services on Windows.
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $Root "storage\logs\demo"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: .venv not found. Run .\scripts\dev-bootstrap.ps1 first" -ForegroundColor Red
    exit 1
}

function Test-PortListening {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

function Die {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

$portMap = @{
    8000 = "local-api"
    8081 = "local-panel"
    8090 = "owner-admin"
}
foreach ($port in $portMap.Keys) {
    if (Test-PortListening $port) {
        Die "Port $port is already in use ($($portMap[$port])). Run .\scripts\stop-demo.ps1"
    }
}

foreach ($app in @("local-api", "local-panel", "owner-admin")) {
    $envFile = Join-Path $Root "apps\$app\.env"
    if (-not (Test-Path $envFile)) {
        Die "Missing apps/$app/.env. Run .\scripts\dev-bootstrap.ps1"
    }
}

foreach ($app in @("local-panel", "owner-admin")) {
    $vendor = Join-Path $Root "apps\$app\vendor\autoload.php"
    if (-not (Test-Path $vendor)) {
        Die "Missing vendor for apps/$app. Run .\scripts\dev-bootstrap.ps1"
    }
}

Write-Host "==> Starting demo services" -ForegroundColor Cyan

$apiDir = Join-Path $Root "apps\local-api"
$panelDir = Join-Path $Root "apps\local-panel"
$ownerDir = Join-Path $Root "apps\owner-admin"

$apiLog = Join-Path $LogDir "local-api.log"
$panelLog = Join-Path $LogDir "local-panel.log"
$ownerLog = Join-Path $LogDir "owner-admin.log"

$apiWrapper = Join-Path $LogDir "start-api.ps1"
$panelWrapper = Join-Path $LogDir "start-panel.ps1"
$ownerWrapper = Join-Path $LogDir "start-owner.ps1"

Set-Content -Path $apiWrapper -Encoding ASCII -Value @(
    "Set-Location '$apiDir'"
    "& '$VenvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 *>> '$apiLog' 2>&1"
)
Set-Content -Path $panelWrapper -Encoding ASCII -Value @(
    "Set-Location '$panelDir'"
    "php artisan serve --host=127.0.0.1 --port=8081 *>> '$panelLog' 2>&1"
)
Set-Content -Path $ownerWrapper -Encoding ASCII -Value @(
    "Set-Location '$ownerDir'"
    "php artisan serve --host=127.0.0.1 --port=8090 *>> '$ownerLog' 2>&1"
)

$apiProc = Start-Process powershell -ArgumentList @(
    "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", $apiWrapper
) -PassThru

Start-Sleep -Seconds 2

$panelProc = Start-Process powershell -ArgumentList @(
    "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", $panelWrapper
) -PassThru

$ownerProc = Start-Process powershell -ArgumentList @(
    "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", $ownerWrapper
) -PassThru

$pidFile = Join-Path $LogDir "pids.json"
@{
    api     = $apiProc.Id
    panel   = $panelProc.Id
    owner   = $ownerProc.Id
    started = (Get-Date -Format o)
} | ConvertTo-Json | Set-Content -Path $pidFile -Encoding ASCII

Write-Host "  local-api     PID $($apiProc.Id)  -> http://127.0.0.1:8000"
Write-Host "  local-panel   PID $($panelProc.Id)  -> http://127.0.0.1:8081/login"
Write-Host "  owner-admin   PID $($ownerProc.Id)  -> http://127.0.0.1:8090"
Write-Host ""
Write-Host "Logs: $LogDir"
Write-Host ""
Write-Host "Operator panel:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:8081/login"
Write-Host "  operator@demo.local / demo"
Write-Host ""
Write-Host "Smoke test: .\scripts\demo-smoke.ps1"
Write-Host "Stop demo:  .\scripts\stop-demo.ps1"
