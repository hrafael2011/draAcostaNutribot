#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="${DIET_AGENT_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Colores
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}ℹ${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; exit 1; }

cleanup() {
  echo ""
  info "Deteniendo servicios..."
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null && ok "Backend detenido"
}
trap cleanup EXIT

echo ""
echo -e "${CYAN}══════════════════════════════════════${NC}"
echo -e "${CYAN}  Dra. Acosta Nutribot — Dev Launcher ${NC}"
echo -e "${CYAN}══════════════════════════════════════${NC}"
echo ""

# ── 1. PostgreSQL ──────────────────────────────────────
info "[1/3] Iniciando PostgreSQL..."
cd "$ROOT"
docker compose up -d db 2>/dev/null || fail "Docker no está corriendo. Abre Docker Desktop e intenta de nuevo."
echo -n "  Esperando DB..."
until docker compose exec db pg_isready -U postgres -d diet_agent &>/dev/null; do
  sleep 1
done
ok "PostgreSQL listo en localhost:5434"

# ── 2. Backend ──────────────────────────────────────────
echo ""
info "[2/3] Iniciando backend (uvicorn) en puerto $BACKEND_PORT..."
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  fail "No existe backend/.venv — ejecuta: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
fi
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
cd "$ROOT"
# Esperar a que responda health check
for i in $(seq 1 15); do
  if curl -sf "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
    ok "Backend listo → http://localhost:$BACKEND_PORT"
    ok "API docs → http://localhost:$BACKEND_PORT/docs"
    break
  fi
  sleep 1
done
if ! curl -sf "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
  fail "Backend no respondió — revisá logs con 'cd backend && source .venv/bin/activate && uvicorn app.main:app --reload'"
fi

# ── 3. Frontend ─────────────────────────────────────────
echo ""
info "[3/3] Iniciando frontend (Vite) en puerto $FRONTEND_PORT..."
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
  info "Instalando dependencias del frontend (primera vez)..."
  npm install
fi
echo ""
echo -e "  ${GREEN}Frontend :${NC} http://localhost:$FRONTEND_PORT"
echo -e "  ${GREEN}Backend  :${NC} http://localhost:$BACKEND_PORT"
echo -e "  ${GREEN}API docs :${NC} http://localhost:$BACKEND_PORT/docs"
echo ""
warn "Presiona Ctrl+C para detener todos los servicios"
echo ""

npm run dev

# cleanup() se ejecuta automáticamente al salir
