# Start the NIYAM API and web app, open the browser, and stop both on Ctrl+C.
# Creates backend\.venv itself (with Python 3.11 or 3.12; never falls back to a newer default `python`).
# Needs frontend\node_modules (npm ci).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root "backend\.venv"
$python = Join-Path $venv "Scripts\python.exe"
$apiUrl = "http://127.0.0.1:8000"
$appUrl = "http://localhost:5173"

# The backend needs Python 3.11 or 3.12 (requires-python = ">=3.11,<3.13" in backend\pyproject.toml).
# `py` (the Windows launcher) picks an exact version; a bare `python` is used only if it is already 3.11 or 3.12.
function Find-SupportedPython {
    foreach ($spec in @("-3.11", "-3.12")) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            try { & py $spec --version *> $null; if ($LASTEXITCODE -eq 0) { return @("py", $spec) } } catch {}
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $v = (& python -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null)
        if ($v -eq "3.11" -or $v -eq "3.12") { return @("python") }
    }
    return $null
}

if (-not (Test-Path $python)) {
    $launcher = Find-SupportedPython
    if (-not $launcher) {
        Write-Host "No Python 3.11 or 3.12 found: install one (e.g. from python.org) and re-run."
        exit 1
    }
    Write-Host "Creating backend\.venv with $($launcher -join ' ')..."
    $launcherArgs = @()
    if ($launcher.Length -gt 1) { $launcherArgs = $launcher[1..($launcher.Length - 1)] }
    & $launcher[0] @launcherArgs -m venv $venv
    & $python -m pip install -q -e "$(Join-Path $root 'backend')[dev]"
}
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
