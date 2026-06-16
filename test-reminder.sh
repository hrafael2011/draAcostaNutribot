#!/usr/bin/env bash
# Ejecuta los recordatorios manualmente para pruebas.
# Crea una dieta y luego corre este script para ver el email al instante.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"

if [ ! -d .venv ]; then
  echo "❌ No existe backend/.venv"
  exit 1
fi

source .venv/bin/activate

# Usar REMINDER_DAYS=0 para capturar todas las dietas sin recordatorio
export REMINDER_DAYS=0
export REMINDER_ENABLED=true

echo "🔍 Buscando dietas sin recordatorio..."
python -c "
import asyncio
from app.core.database import async_session_factory
from app.services.reminder_service import check_and_send_reminders

async def main():
    async with async_session_factory() as db:
        sent = await check_and_send_reminders(db)
        if sent:
            print(f'✅ {sent} recordatorio(s) enviado(s)')
        else:
            print('ℹ️  No se encontraron dietas pendientes de recordatorio')

asyncio.run(main())
"