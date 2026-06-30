# Autoscale dev bootstrap for Windows PowerShell.
# Usage:
#   $env:PGUSER = "postgres"
#   $env:PGHOST = "127.0.0.1"
#   $env:PGPORT = "5432"
#   $env:PGPASSWORD = "..."   # optional; prompted if missing
#   .\scripts\dev-bootstrap.ps1
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogFile = Join-Path $Root "bootstrap-run.log"

function Write-Step {
    param([string]$Message)
    $line = "==> $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Die {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Add-Content -Path $LogFile -Value "ERROR: $Message"
    exit 1
}

function UrlEncode {
    param([string]$Value)
    return [System.Uri]::EscapeDataString($Value)
}

function Ensure-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Die "$Name not found in PATH"
    }
}

function Set-EnvFileValue {
    param(
        [string]$FilePath,
        [string]$Key,
        [string]$Value
    )
    $found = $false
    if (Test-Path $FilePath) {
        $newLines = foreach ($line in (Get-Content $FilePath)) {
            if ($line -match "^$([regex]::Escape($Key))=") {
                $found = $true
                "$Key=$Value"
            } else {
                $line
            }
        }
        if (-not $found) {
            $newLines += "$Key=$Value"
        }
        Set-Content -Path $FilePath -Value $newLines -Encoding ASCII
    } else {
        Set-Content -Path $FilePath -Value "$Key=$Value" -Encoding ASCII
    }
}

function Invoke-PsqlCommand {
    param([string[]]$PsqlArgs)
    $env:PGPASSWORD = $script:PgPassword
    & psql @PsqlArgs
    if ($LASTEXITCODE -ne 0) {
        Die "psql exited with code $LASTEXITCODE"
    }
}

function Get-PsqlScalar {
    param(
        [string]$Sql,
        [string]$Database = "postgres"
    )
    $env:PGPASSWORD = $script:PgPassword
    $result = & psql -h $script:PgHost -p $script:PgPort -U $script:PgUser -d $Database -tAc $Sql 2>&1
    if ($LASTEXITCODE -ne 0) {
        Die "psql failed: $result"
    }
    return ($result | Out-String).Trim()
}

function Ensure-LaravelAppKey {
    param([string]$AppDir)
    $envPath = Join-Path $AppDir ".env"
    if (-not (Test-Path $envPath)) {
        return
    }
    $hasKey = Select-String -Path $envPath -Pattern "^APP_KEY=.+" -Quiet
    if ($hasKey) {
        return
    }
    $hasEmptyKey = Select-String -Path $envPath -Pattern "^APP_KEY=" -Quiet
    if (-not $hasEmptyKey) {
        Add-Content -Path $envPath -Value "APP_KEY=" -Encoding ASCII
    }
    Push-Location $AppDir
    php artisan key:generate --force 2>&1 | Out-Host
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) {
        Die "php artisan key:generate failed in $AppDir"
    }
}

$script:PgHost = if ($env:PGHOST) { $env:PGHOST } else { "127.0.0.1" }
$script:PgPort = if ($env:PGPORT) { $env:PGPORT } else { "5432" }
$script:PgUser = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
$script:PgPassword = if ($env:PGPASSWORD) { $env:PGPASSWORD } else { $null }
$LocalDbName = if ($env:LOCAL_DB_NAME) { $env:LOCAL_DB_NAME } else { "autoscale_local" }
$OwnerDbName = if ($env:OWNER_DB_NAME) { $env:OWNER_DB_NAME } else { "autoscale_owner" }

Set-Content -Path $LogFile -Value "Bootstrap started $(Get-Date -Format o)" -Encoding ASCII

Write-Step "Checking dependencies"
Ensure-Command psql
Ensure-Command php
Ensure-Command composer

$PythonExe = $null
foreach ($candidate in @("py -3.11", "py -3.12", "python", "python3")) {
    $parts = $candidate -split " ", 2
    if ($parts.Count -eq 2) {
        $cmd = Get-Command $parts[0] -ErrorAction SilentlyContinue
        if ($cmd) {
            $ver = & $parts[0] $parts[1] -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $ver) {
                $PythonExe = $ver.Trim()
                break
            }
        }
    } else {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            $PythonExe = $cmd.Source
            break
        }
    }
}
if (-not $PythonExe) {
    Die "Python 3.11+ not found (try py -3.11 or python)"
}
Write-Host "  Python: $PythonExe"

if (-not $script:PgPassword) {
    $secure = Read-Host "PostgreSQL password for user $script:PgUser" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $script:PgPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}
$env:PGPASSWORD = $script:PgPassword

$pgTarget = "$($script:PgUser)@$($script:PgHost):$($script:PgPort)"
Write-Step "Checking PostgreSQL ($pgTarget)"
$ping = Get-PsqlScalar "SELECT 1"
if ($ping -ne "1") {
    Die "Cannot connect to PostgreSQL at $pgTarget"
}

Write-Step "Creating databases (if missing)"
foreach ($db in @($LocalDbName, $OwnerDbName)) {
    $exists = Get-PsqlScalar "SELECT 1 FROM pg_database WHERE datname = '$db'"
    if ($exists -eq "1") {
        Write-Host "  Database $db already exists"
    } else {
        Invoke-PsqlCommand @(
            "-h", $script:PgHost,
            "-p", $script:PgPort,
            "-U", $script:PgUser,
            "-d", "postgres",
            "-c", "CREATE DATABASE $db"
        )
        Write-Host "  Created database $db"
    }
}

Write-Step "Python venv and packages"
$VenvDir = Join-Path $Root ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    & $PythonExe -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Die "Failed to create venv" }
}
$Pip = Join-Path $VenvDir "Scripts\pip.exe"
$Alembic = Join-Path $VenvDir "Scripts\alembic.exe"

& $VenvPython -m pip install -q --upgrade pip
$packages = @(
    (Join-Path $Root "packages\license-core"),
    (Join-Path $Root "packages\hardware-core"),
    (Join-Path $Root "packages\terminal-drivers"),
    (Join-Path $Root "packages\camera-core"),
    (Join-Path $Root "packages\alpr-core"),
    (Join-Path $Root "apps\local-api"),
    "psycopg2-binary",
    "email-validator",
    "pytest",
    "pytest-asyncio",
    "httpx"
)
& $Pip install -q @packages
$terminalDrivers = Join-Path $Root "packages\terminal-drivers"
& $Pip install -q ($terminalDrivers + "[hardware]")
if ($LASTEXITCODE -ne 0) { Die "pip install failed" }

Write-Step "Composer (local-panel, owner-admin)"
foreach ($app in @("local-panel", "owner-admin")) {
    $vendor = Join-Path $Root "apps\$app\vendor\autoload.php"
    if (-not (Test-Path $vendor)) {
        Write-Host "  composer install in apps/$app"
        Push-Location (Join-Path $Root "apps\$app")
        composer install --no-interaction --prefer-dist
        if ($LASTEXITCODE -ne 0) { Pop-Location; Die "composer install failed for $app" }
        Pop-Location
    }
}

Write-Step "Ed25519 keys"
$KeysFile = Join-Path $Root ".env.dev.keys"
if (-not (Test-Path $KeysFile)) {
    $keyOutput = & $VenvPython (Join-Path $Root "apps\local-api\scripts\generate_keys.py")
    Set-Content -Path $KeysFile -Value ($keyOutput -join "`n") -Encoding ASCII
    Write-Host "  Keys saved to $KeysFile"
}
$keysContent = Get-Content $KeysFile -Raw
$LicensePrivate = ""
$LicensePublic = ""
foreach ($line in ($keysContent -split "`n")) {
    if ($line -match "^LICENSE_SIGNING_PRIVATE_KEY=(.+)$") { $LicensePrivate = $Matches[1].Trim() }
    if ($line -match "^LICENSE_PUBLIC_KEY=(.+)$") { $LicensePublic = $Matches[1].Trim() }
}
if (-not $LicensePrivate -or -not $LicensePublic) {
    Die "LICENSE_SIGNING_PRIVATE_KEY or LICENSE_PUBLIC_KEY empty in $KeysFile"
}

Write-Step "local-api .env"
$ApiEnv = Join-Path $Root "apps\local-api\.env"
if (-not (Test-Path $ApiEnv)) {
    Copy-Item (Join-Path $Root "apps\local-api\.env.example") $ApiEnv
}
if ($script:PgPassword) {
    $encPass = UrlEncode $script:PgPassword
    $dbUrl = "postgresql+asyncpg://$($script:PgUser):$encPass@$($script:PgHost):$($script:PgPort)/$LocalDbName"
} else {
    $dbUrl = "postgresql+asyncpg://$($script:PgUser)@$($script:PgHost):$($script:PgPort)/$LocalDbName"
}
Set-EnvFileValue $ApiEnv "DATABASE_URL" $dbUrl
Set-EnvFileValue $ApiEnv "LICENSE_PUBLIC_KEY" $LicensePublic
$CorsOrigins = "http://127.0.0.1:8081,http://localhost:8081,http://127.0.0.1:8080,http://localhost:8080"
Set-EnvFileValue $ApiEnv "CORS_ORIGINS" $CorsOrigins

Write-Step "Alembic migrate + seed"
$env:DEV_LICENSE_PRIVATE_KEY = $LicensePrivate
$env:LICENSE_SIGNING_PRIVATE_KEY = $LicensePrivate
$env:LICENSE_PUBLIC_KEY = $LicensePublic
Push-Location (Join-Path $Root "apps\local-api")
& $Alembic upgrade head
if ($LASTEXITCODE -ne 0) { Pop-Location; Die "alembic upgrade head failed" }
& $VenvPython scripts\seed_demo.py
if ($LASTEXITCODE -ne 0) { Pop-Location; Die "seed_demo.py failed" }
Pop-Location

Write-Step "Verifying tables in $LocalDbName"
$tableSql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
$tableCount = [int](Get-PsqlScalar $tableSql $LocalDbName)
if ($tableCount -le 0) {
    Die "$LocalDbName has no tables after migration"
}
Write-Host "  Table count: $tableCount"

Write-Step "owner-admin .env"
$OwnerDir = Join-Path $Root "apps\owner-admin"
$OwnerEnv = Join-Path $OwnerDir ".env"
if (-not (Test-Path $OwnerEnv)) {
    Copy-Item (Join-Path $Root "apps\owner-admin\.env.example") $OwnerEnv
}
Ensure-LaravelAppKey $OwnerDir
Set-EnvFileValue $OwnerEnv "DB_CONNECTION" "pgsql"
Set-EnvFileValue $OwnerEnv "DB_HOST" $script:PgHost
Set-EnvFileValue $OwnerEnv "DB_PORT" $script:PgPort
Set-EnvFileValue $OwnerEnv "DB_DATABASE" $OwnerDbName
Set-EnvFileValue $OwnerEnv "DB_USERNAME" $script:PgUser
Set-EnvFileValue $OwnerEnv "DB_PASSWORD" $script:PgPassword
Set-EnvFileValue $OwnerEnv "LICENSE_SIGNING_PRIVATE_KEY" $LicensePrivate
Set-EnvFileValue $OwnerEnv "LICENSE_PUBLIC_KEY" $LicensePublic

Write-Step "owner-admin migrate + seed"
Push-Location $OwnerDir
php artisan migrate --force
if ($LASTEXITCODE -ne 0) { Pop-Location; Die "owner-admin migrate failed" }
php artisan db:seed --force
if ($LASTEXITCODE -ne 0) { Pop-Location; Die "owner-admin db:seed failed" }
Pop-Location

Write-Step "local-panel .env"
$PanelDir = Join-Path $Root "apps\local-panel"
$PanelEnv = Join-Path $PanelDir ".env"
if (-not (Test-Path $PanelEnv)) {
    Copy-Item (Join-Path $Root "apps\local-panel\.env.example") $PanelEnv
}
Ensure-LaravelAppKey $PanelDir
Set-EnvFileValue $PanelEnv "LOCAL_API_URL" "http://127.0.0.1:8000"
Set-EnvFileValue $PanelEnv "LOCAL_API_WS_URL" "ws://127.0.0.1:8000"
Set-EnvFileValue $PanelEnv "SESSION_DRIVER" "file"
Set-EnvFileValue $PanelEnv "APP_URL" "http://127.0.0.1:8081"

Write-Host ""
Write-Host "Bootstrap complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  .\scripts\start-demo.ps1"
Write-Host "  .\scripts\demo-smoke.ps1"
Write-Host "  .\scripts\demo-smoke.ps1 -Full"
