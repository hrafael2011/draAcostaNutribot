# Simplificación del Entorno de Desarrollo

**Fecha:** 2026-06-12
**Objetivo:** Eliminar Docker para frontend/backend, usar entornos nativos (npm + venv), Docker solo para PostgreSQL.

---

## Cambios

### 1. `docker-compose.yml` — Solo PostgreSQL
- Eliminar servicios: `backend`, `web`, `ngrok`
- Mantener solo `db` (postgres:16-alpine, puerto 5434, volumen pgdata)

### 2. Archivos a eliminar
- `docker/web.Dockerfile`
- `docker/nginx.conf`
- `docker/` (directorio completo, ya vacío tras eliminar los archivos)
- `backend/Dockerfile`
- `backend/docker-entrypoint.sh`

### 3. `start.sh` — Script único (nuevo)
Levanta DB → backend → frontend en secuencia:
```bash
#!/bin/bash
docker compose up -d db
until docker compose exec db pg_isready -U postgres 2>/dev/null; do sleep 1; done
echo "DB ready"
cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
cd frontend && npm run dev
```

### 4. `backend/.env` — Limpiar
- Eliminar `NGROK_AUTHTOKEN`
- Mantener todo lo demás (DATABASE_URL, OPENAI_*, JWT_SECRET, CORS_ORIGINS)

### 5. `scripts/start-backend.sh` — Actualizar
- Mantener pero simplificar: usar puerto 8001, verificar `.venv`

### 6. `scripts/sync-telegram-webhook.sh` — Archivar
- Telegram fue removido en migración 0007, el script ya no funciona

---

## Verificación
- [ ] `docker compose up -d db` — solo PostgreSQL inicia
- [ ] `cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8001` — backend responde en `:8001/api/health`
- [ ] `cd frontend && npm run dev` — frontend en `:5173`
- [ ] Login funciona, genera dieta, descarga PDF
- [ ] `./start.sh` levanta todo con un comando
