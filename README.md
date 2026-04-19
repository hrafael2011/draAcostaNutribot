# draAcostaNutribot

**Diet Telegram Agent** — web admin panel and Telegram bot for a nutrition practice: patient intake links, clinical profiles, AI-assisted diet generation, and a conversational assistant for the doctor on Telegram.

## Architecture

- **Backend** (`backend/`): FastAPI, SQLAlchemy 2 (async), PostgreSQL, Alembic migrations.
- **Frontend** (`frontend/`): React 19, Vite, TypeScript — admin UI for patients, diets, and Telegram linking.
- **Deploy**: See [DEPLOYMENT.md](./DEPLOYMENT.md) for Railway (API + DB), Vercel (frontend), and optional ngrok for webhooks.

## Quick start (local)

1. Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env.local`.
2. Start PostgreSQL (or use Docker Compose from the repo root).
3. Backend: `./scripts/start-backend.sh` or `cd backend && uvicorn app.main:app --reload --port 8001`.
4. Frontend: `cd frontend && npm install && npm run dev`.

API base path: `/api`. Health: `GET /api/health`, readiness (DB): `GET /api/health/ready`.

## Security notes

- Production requires a strong `JWT_SECRET` and `TELEGRAM_WEBHOOK_SECRET` (validated at startup).
- Doctor self-registration is allowed only while **no** doctor exists in the database (single-tenant / one practice).

## License

See [LICENSE](./LICENSE).
