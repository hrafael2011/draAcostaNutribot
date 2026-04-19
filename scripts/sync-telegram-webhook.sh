#!/usr/bin/env bash
# Lee la URL HTTPS del túnel ngrok (API local :4040) y registra el webhook en Telegram.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Falta $ENV_FILE"
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "TELEGRAM_BOT_TOKEN vacío en backend/.env"
  exit 1
fi

resolve_webhook_base_url() {
  if [ -n "${WEBHOOK_PUBLIC_BASE_URL:-}" ]; then
    printf '%s\n' "${WEBHOOK_PUBLIC_BASE_URL%/}"
    return 0
  fi

  # Túnel del diet agent (docker compose `ngrok` → :14040). Evita usar :4040 de otro proyecto.
  NGROK_API_BASE="${NGROK_AGENT_API:-http://127.0.0.1:14040}"
  TUNNEL_JSON=$(curl -sS "${NGROK_API_BASE}/api/tunnels" 2>/dev/null || echo '{"tunnels":[]}')
  TUNNEL=""
  if TUNNEL=$(echo "$TUNNEL_JSON" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for t in d.get('tunnels', []):
    u = t.get('public_url') or ''
    if u.startswith('https://'):
        print(u)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null); then
    printf '%s\n' "$TUNNEL"
    return 0
  fi

  echo "No hay túnel HTTPS en ${NGROK_API_BASE}."
  echo "Con Docker Compose: docker compose up -d ngrok   (túnel → servicio web, API local :14040)"
  echo "Producción: WEBHOOK_PUBLIC_BASE_URL=https://tu-backend.up.railway.app ./scripts/sync-telegram-webhook.sh"
  echo "Sin Compose: NGROK_AGENT_API=http://127.0.0.1:4040 ./scripts/sync-telegram-webhook.sh"
  exit 1
}

BASE_URL="$(resolve_webhook_base_url)"
URL="${BASE_URL}/api/telegram/webhook"
echo "Webhook → $URL"
code="$(curl -sS -o /dev/null -w "%{http_code}" -X POST "$URL" -H "Content-Type: application/json" -d '{}' || echo "000")"
if [ "$code" != "200" ]; then
  echo "ERROR: el endpoint no responde 200 a POST $URL (código $code). Revisa ngrok o tu dominio público."
  exit 1
fi
if [ -n "${TELEGRAM_WEBHOOK_SECRET:-}" ]; then
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    --data-urlencode "url=${URL}" \
    --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET}" | python3 -m json.tool
else
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    --data-urlencode "url=${URL}" | python3 -m json.tool
fi
echo ""
echo "getWebhookInfo:"
curl -sS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
