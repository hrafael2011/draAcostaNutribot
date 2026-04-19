#!/usr/bin/env bash
# Volcado SQL de la base diet_agent del servicio Docker Compose `db`.
# Uso (desde la raíz del repo): ./scripts/backup-db.sh [ruta_salida.sql]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/backups/diet_agent_$(date +%Y%m%d_%H%M%S).sql}"
mkdir -p "$(dirname "$OUT")"
cd "$ROOT"
docker compose exec -T db pg_dump -U postgres diet_agent >"$OUT"
echo "Backup escrito: $OUT"
