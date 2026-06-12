#!/bin/sh
set -e
cd /app
PORT="${PORT:-8000}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "[backend] Alembic upgrade..."
  alembic upgrade head
else
  echo "[backend] Skipping Alembic upgrade (RUN_MIGRATIONS=${RUN_MIGRATIONS})"
fi

echo "[backend] Uvicorn on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
