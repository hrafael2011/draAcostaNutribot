#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="${DIET_AGENT_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "========================================="
echo "  Dra. Acosta Nutribot — Dev Environment"
echo "========================================="

# 1. PostgreSQL
echo ""
echo "[1/3] Starting PostgreSQL..."
cd "$ROOT"
docker compose up -d db
echo -n "  Waiting for DB..."
until docker compose exec db pg_isready -U postgres -d diet_agent &>/dev/null; do
  sleep 1
done
echo " ready"

# 2. Backend
echo ""
echo "[2/3] Starting backend (uvicorn) on port $BACKEND_PORT..."
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  echo "  ERROR: backend/.venv not found. Run: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# 3. Frontend
echo ""
echo "[3/3] Starting frontend (Vite) on port $FRONTEND_PORT..."
echo ""
echo "  Frontend : http://localhost:$FRONTEND_PORT"
echo "  Backend  : http://localhost:$BACKEND_PORT"
echo "  API docs : http://localhost:$BACKEND_PORT/docs"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

cd "$ROOT/frontend"
npm run dev

# Cleanup on Ctrl+C
kill $BACKEND_PID 2>/dev/null
echo "All services stopped."
