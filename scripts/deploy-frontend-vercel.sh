#!/usr/bin/env bash
# Deploy del panel (Vite) a Vercel en producción.
# Requiere: export VERCEL_TOKEN="..." (no lo pegues en chats).
# Opcional: VITE_API_BASE_URL (por defecto el backend Railway del proyecto).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "Falta VERCEL_TOKEN. Ejemplo: export VERCEL_TOKEN=\"...\""
  exit 1
fi

VITE_API_BASE_URL="${VITE_API_BASE_URL:-https://diet-backend-production-9360.up.railway.app/api}"
VERCEL_TEAM="${VERCEL_TEAM:-hrafael2011s-projects}"
VERCEL_PROJECT="${VERCEL_PROJECT:-diet-telegram-agent}"

echo "VITE_API_BASE_URL=$VITE_API_BASE_URL"
echo "Vercel team=$VERCEL_TEAM project=$VERCEL_PROJECT"

npm ci

npx vercel@latest link \
  --yes \
  --non-interactive \
  --team "$VERCEL_TEAM" \
  --project "$VERCEL_PROJECT" \
  -t "$VERCEL_TOKEN"

npx vercel@latest deploy \
  --prod \
  --yes \
  --non-interactive \
  -S "$VERCEL_TEAM" \
  -t "$VERCEL_TOKEN" \
  -b "VITE_API_BASE_URL=$VITE_API_BASE_URL"

echo ""
echo "Listo. En Railway, pon CORS_ORIGINS a la URL que te mostró Vercel (https://....vercel.app)."
