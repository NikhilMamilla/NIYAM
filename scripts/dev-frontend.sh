#!/usr/bin/env bash
# Start the Vite dev server on http://localhost:5173 (proxies /api to the backend on 127.0.0.1:8000).
set -euo pipefail
cd "$(dirname "$0")/../frontend"
[ -d node_modules ] || npm ci
npm run dev
