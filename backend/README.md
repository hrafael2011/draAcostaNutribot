# Backend

FastAPI service for **diet_telegram_agent**: JWT auth, patient and diet APIs, public intake links, Telegram webhook and bot logic, PDF export.

## Stack

- Python 3.12+
- FastAPI, Uvicorn
- SQLAlchemy 2 (async) + asyncpg
- PostgreSQL, Alembic
- OpenAI API (diet generation / intent assist)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

## Configuration

See `.env.example`. Important variables:

| Variable | Notes |
|----------|--------|
| `ENV` | `development` vs `production` — production enforces `JWT_SECRET` and `TELEGRAM_WEBHOOK_SECRET`. |
| `DATABASE_URL` | Async URL (`postgresql+asyncpg://...`) or plain `postgresql://` (normalized at startup). |
| `CORS_ORIGINS` | Comma-separated origins or `*` (dev only). |
| `TELEGRAM_WEBHOOK_SECRET` | Must match `X-Telegram-Bot-Api-Secret-Token` on webhook requests in production. |

## Health

- `GET /api/health` — process up.
- `GET /api/health/ready` — database connectivity.

## Tests

```bash
pytest -q
```
