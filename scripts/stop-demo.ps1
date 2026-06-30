# Stop Autoscale demo services on Windows (ports 8000, 8081, 8090).
#Requires -Version 5.1
$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $Root "storage\logs\demo"
$PidFile = Join-Path $LogDir "pids.json"

function Stop-ProcessOnPort {
    param([int]$Port)
    $found = $false
    $lines = netstat -ano | Select-String ":$Port\s"
    foreach ($line in $lines) {
        $parts = ($line.ToString().Trim() -split '\s+')
        if ($parts.Length -lt 5) { continue }
        $procId = $parts[-1]
        if ($procId -match '^\d+$' -and [int]$procId -gt 0) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Stopping PID $procId on port $Port ($($proc.ProcessName))"
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                $found = $true
            }
        }
    }
    if (-not $found) {
        Write-Host "  Port $Port - no process found"
    }
}

Write-Host "==> Stopping demo services"

if (Test-Path $PidFile) {
    try {
        $pids = Get-Content $PidFile -Raw | ConvertFrom-Json
        foreach ($name in @("api", "panel", "owner")) {
            $id = $pids.$name
            if ($id) {
                $proc = Get-Process -Id $id -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  Stopping $name PID $id"
                    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
                }
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Could not read $PidFile"
    }
}

foreach ($port in @(8000, 8081, 8090)) {
    Stop-ProcessOnPort $port
}

Write-Host "Demo stopped."
