# Autoscale demo smoke test for Windows. Exit 0 = demo ready.
param(
    [switch]$Full
)
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Api = if ($env:API_URL) { $env:API_URL } else { "http://127.0.0.1:8000" }
$Panel = if ($env:PANEL_URL) { $env:PANEL_URL } else { "http://127.0.0.1:8081" }
$Owner = if ($env:OWNER_URL) { $env:OWNER_URL } else { "http://127.0.0.1:8090" }

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

function Fail {
    param([string]$Message)
    Write-Host "FAIL: $Message" -ForegroundColor Red
    exit 1
}

function Ok {
    param([string]$Message)
    Write-Host "OK: $Message" -ForegroundColor Green
}

function To-JsonString {
    param($Object)
    return ($Object | ConvertTo-Json -Compress -Depth 20)
}

function Invoke-ApiGet {
    param(
        [string]$Url,
        [hashtable]$Headers = @{}
    )
    $params = @{
        Uri             = $Url
        Method          = "Get"
        UseBasicParsing = $true
    }
    if ($Headers.Count -gt 0) {
        $params.Headers = $Headers
    }
    $response = Invoke-WebRequest @params
    return $response.Content
}

function Invoke-ApiPost {
    param(
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    $params = @{
        Uri             = $Url
        Method          = "Post"
        ContentType     = "application/json"
        UseBasicParsing = $true
    }
    if ($Headers.Count -gt 0) {
        $params.Headers = $Headers
    }
    if ($Body) {
        $params.Body = $Body
    }
    $response = Invoke-WebRequest @params
    return $response.Content
}

function Invoke-PyCheck {
    param(
        [string]$Script,
        [string]$Json
    )
    $Json | & $Python -c $Script
    if ($LASTEXITCODE -ne 0) {
        throw "python check failed"
    }
}

function Invoke-PyExpr {
    param(
        [string]$Script,
        [string]$Json
    )
    $out = $Json | & $Python -c $Script
    if ($LASTEXITCODE -ne 0) {
        throw "python expr failed"
    }
    return ($out | Out-String).Trim()
}

Write-Host "==> local-api health"
try {
    $healthRaw = Invoke-ApiGet "$Api/api/health"
} catch {
    Fail "local-api not reachable at $Api"
}
try {
    Invoke-PyCheck "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='ok', d" $healthRaw
} catch {
    Fail "health status != ok"
}
Ok "health"

try {
    $licValid = Invoke-PyExpr "import json,sys; print(json.load(sys.stdin).get('license',{}).get('valid',False))" $healthRaw
} catch {
    Fail "failed to parse health JSON"
}
if ($licValid -ne "True") {
    Fail "license not valid in health"
}
Ok "license valid"

Write-Host "==> local-panel"
try {
    Invoke-ApiGet "$Panel/login" | Out-Null
} catch {
    Fail "local-panel not reachable at $Panel/login"
}
Ok "panel /login"

Write-Host "==> owner-admin"
$ownerOk = $false
try {
    Invoke-ApiGet $Owner | Out-Null
    $ownerOk = $true
} catch {
    $ownerOk = $false
}
if (-not $ownerOk) {
    try {
        Invoke-ApiGet "$Owner/admin" | Out-Null
        $ownerOk = $true
    } catch {
        Fail "owner-admin not reachable at $Owner"
    }
}
Ok "owner-admin"

Write-Host "==> API auth + resources"
try {
    $loginRaw = Invoke-ApiPost "$Api/api/auth/login" -Body '{"email":"operator@demo.local","password":"demo"}'
} catch {
    Fail "login operator@demo.local"
}
$token = Invoke-PyExpr "import json,sys; print(json.load(sys.stdin)['access_token'])" $loginRaw
$auth = @{ Authorization = "Bearer $token" }

try {
    $licRaw = Invoke-ApiGet "$Api/api/license/status" -Headers $auth
    $licCheck = "import json,sys; d=json.load(sys.stdin); assert d.get('valid'), d; mods=set(d.get('modules',[])); need={'core','terminals','cameras','alpr','workplaces','weighing_journal'}; assert need<=mods, mods"
    Invoke-PyCheck $licCheck $licRaw
} catch {
    Fail "license modules incomplete"
}
Ok "license modules"

$terminalsRaw = Invoke-ApiGet "$Api/api/terminals" -Headers $auth
try {
    Invoke-PyCheck "import json,sys; t=json.load(sys.stdin); assert any(x.get('name')=='DEMO Terminal' for x in t), t" $terminalsRaw
} catch {
    Fail "DEMO Terminal not found"
}
Ok "DEMO Terminal"

$camerasRaw = Invoke-ApiGet "$Api/api/cameras" -Headers $auth
try {
    Invoke-PyCheck "import json,sys; c=json.load(sys.stdin); assert any(x.get('name')=='DEMO Camera' for x in c), c" $camerasRaw
} catch {
    Fail "DEMO Camera not found"
}
Ok "DEMO Camera"

$workplacesRaw = Invoke-ApiGet "$Api/api/workplaces" -Headers $auth
$wpId = Invoke-PyExpr "import json,sys; w=json.load(sys.stdin); lane=next((x for x in w if x.get('name')=='Demo Lane'), None); assert lane, w; print(lane['id'])" $workplacesRaw
if (-not $wpId) { Fail "Demo Lane not found" }
Ok "Demo Lane ($wpId)"

$tid = Invoke-PyExpr "import json,sys; t=json.load(sys.stdin); demo=next(x for x in t if x['name']=='DEMO Terminal'); print(demo['id'])" $terminalsRaw
try {
    Invoke-ApiPost "$Api/api/terminals/$tid/test" -Headers $auth | Out-Null
} catch {
    Fail "terminal test failed"
}
Ok "DEMO terminal test"

try {
    $alprRaw = Invoke-ApiPost "$Api/api/cameras/alpr/test?provider=demo" -Headers $auth
    Invoke-PyCheck "import json,sys; d=json.load(sys.stdin); c=d.get('candidates',[]); assert c and c[0].get('plate_normalized')=='A123BC77', d" $alprRaw
} catch {
    Fail "demo ALPR != A123BC77"
}
Ok "demo ALPR A123BC77"

$journalRaw = Invoke-ApiGet "$Api/api/weighings" -Headers $auth
$count = Invoke-PyExpr "import json,sys; print(len(json.load(sys.stdin)))" $journalRaw

if ($Full) {
    Write-Host "==> full demo cycle (start workplace, wait ~10s)"
    try {
        Invoke-ApiPost "$Api/api/workplaces/$wpId/start" -Headers $auth | Out-Null
    } catch {
        Fail "workplace start failed"
    }
    Start-Sleep -Seconds 10
    $journalRaw = Invoke-ApiGet "$Api/api/weighings" -Headers $auth
    $fullCheck = "import json,sys; j=json.load(sys.stdin); assert j, 'journal empty'; r=j[0]; assert r.get('plate_normalized')=='A123BC77', r; w=float(r.get('weight',0)); assert 14000<=w<=16000, r"
    try {
        Invoke-PyCheck $fullCheck $journalRaw
    } catch {
        Fail "journal record missing or invalid after full cycle"
    }
    Ok "journal record after full cycle"
} else {
    try {
        Invoke-ApiGet "$Api/api/weighings" -Headers $auth | Out-Null
    } catch {
        Fail "journal endpoint"
    }
    Ok "journal endpoint ($count records)"
    if ([int]$count -gt 0) {
        $journalRaw | & $Python -c "import json,sys; r=json.load(sys.stdin)[0]; assert r.get('plate_normalized'), r; print('  last:', r.get('plate_normalized'), r.get('weight'))"
    }
}

Write-Host ""
Write-Host "Demo smoke: PASS" -ForegroundColor Green
