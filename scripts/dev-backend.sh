#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
source .venv/Scripts/activate
uvicorn app.main:app --reload
