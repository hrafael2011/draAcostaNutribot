#!/usr/bin/env bash
cat <<'EOF'
=== Diet agent + Telegram (ngrok) ===

1) Terminal A — backend en puerto 8001 (no pisa api-backend en 8000):
   ./scripts/start-backend.sh

2) Terminal B — túnel al MISMO puerto:
   ngrok http 8001

3) Terminal C — registrar webhook con la URL que muestre ngrok:
   ./scripts/sync-telegram-webhook.sh

4) Frontend (Vite): usa la API en 8001, p. ej. en frontend/.env.local:
   VITE_API_BASE_URL=http://localhost:8001/api

Variables opcionales:
  export DIET_AGENT_PORT=8010   # otro puerto; ngrok debe usar el mismo númeroEOF
