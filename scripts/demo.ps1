# Start the NIYAM API and web app, open the browser, and stop both on Ctrl+C.
# Needs backend\.venv (pip install -e ".[dev]") and frontend\node_modules (npm ci).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "backend\.venv\Scripts\python.exe"
$apiUrl = "http://127.0.0.1:8000"
$appUrl = "http://localhost:5173"

if (-not (Test-Path $python)) { Write-Host "backend\.venv not found: create it first (see README)"; exit 1 }
if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) { Write-Host "frontend\node_modules not found: run npm ci in frontend\"; exit 1 }

$api = Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory (Join-Path $root "backend") -NoNewWindow -PassThru
$app = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -WorkingDirectory (Join-Path $root "frontend") `
    -NoNewWindow -PassThru
try {
    for ($i = 0; $i -lt 60; $i++) {
        try { Invoke-WebRequest -UseBasicParsing "$apiUrl/health" -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep -Seconds 1 }
    }
    Write-Host "API:     $apiUrl   (health: $apiUrl/health)"
    Write-Host "Web app: $appUrl"
    Write-Host "Press Ctrl+C to stop both."
    Start-Process $appUrl
    while (-not $api.HasExited -and -not $app.HasExited) { Start-Sleep -Seconds 1 }
}
finally {
    Write-Host "stopping"
    foreach ($p in @($api, $app)) {
        if ($p -and -not $p.HasExited) { & taskkill.exe /PID $p.Id /T /F | Out-Null }  # /T also stops node under cmd
    }
}
