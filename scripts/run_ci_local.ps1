# Replica local del job CI en Windows (requiere Docker).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "==> Docker: db + postgrest"
docker compose up -d db postgrest

Write-Host "==> Esperando PostgREST..."
$ok = $false
for ($i = 0; $i -lt 45; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:3001/" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $ok = $true
        break
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) { throw "PostgREST no respondió" }

$env:API_URL = "http://localhost:3001"
$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "==> pytest"
& $py -m pytest tests/ -v --tb=short --junitxml=pytest-results.xml
if ($LASTEXITCODE -ne 0) { throw "pytest falló" }

Write-Host "==> smoke sync KPIs"
& $py scripts/sync_marketing_kpis_cron.py --force

Write-Host "==> CI local OK - ver pytest-results.xml"
