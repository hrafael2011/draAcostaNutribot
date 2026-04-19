#!/usr/bin/env bash
# Arranca diet_telegram_agent en un puerto que NO choque con otros backends (p. ej. api-backend en 8000).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
PORT="${DIET_AGENT_PORT:-8001}"
if [ ! -d .venv ]; then
  echo "Crea el venv: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
echo "Diet Telegram Agent → http://0.0.0.0:${PORT} (health: /api/health)"
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
