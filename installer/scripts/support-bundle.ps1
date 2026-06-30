# Support bundle skeleton
$out = Join-Path $PSScriptRoot "..\..\support-bundle.zip"
$temp = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_.FullName }
Copy-Item (Join-Path $PSScriptRoot "..\..\apps\local-api\data\*.log") $temp -ErrorAction SilentlyContinue
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -OutFile (Join-Path $temp "health.json") -ErrorAction SilentlyContinue
Compress-Archive -Path "$temp\*" -DestinationPath $out -Force
Write-Host "Bundle: $out"
