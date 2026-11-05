#!/usr/bin/env bash
# Start the NIYAM API and web app, open the browser, and stop both on Ctrl+C.
# Needs backend/.venv (pip install -e ".[dev]") and frontend/node_modules (npm ci).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="http://127.0.0.1:8000"
APP_URL="http://localhost:5173"

if [ -x "$ROOT/backend/.venv/bin/python" ]; then PY="$ROOT/backend/.venv/bin/python";
elif [ -x "$ROOT/backend/.venv/Scripts/python.exe" ]; then PY="$ROOT/backend/.venv/Scripts/python.exe";
else echo "backend/.venv not found: create it first (see README)"; exit 1; fi
[ -d "$ROOT/frontend/node_modules" ] || { echo "frontend/node_modules not found: run npm ci in frontend/"; exit 1; }

cleanup() { echo; echo "stopping"; kill "${API_PID:-}" "${APP_PID:-}" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup INT TERM EXIT

(cd "$ROOT/backend" && exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) & API_PID=$!
(cd "$ROOT/frontend" && exec npm run dev) & APP_PID=$!

for _ in $(seq 1 60); do curl -fs "$API_URL/health" >/dev/null 2>&1 && break; sleep 1; done
echo "API:     $API_URL   (health: $API_URL/health)"
echo "Web app: $APP_URL"
echo "Press Ctrl+C to stop both."
if command -v xdg-open >/dev/null; then xdg-open "$APP_URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null; then open "$APP_URL" || true
elif command -v cmd.exe >/dev/null; then cmd.exe /c start "" "$APP_URL" || true; fi
wait
