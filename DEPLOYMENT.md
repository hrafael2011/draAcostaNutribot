# Deployment guide

This project supports two operating modes without sharing the same runtime configuration:

- local development: Docker Compose, `backend/.env`, `frontend/.env.local`, optional ngrok
- production: Railway for the FastAPI backend and PostgreSQL, Vercel for the frontend

## 1. Local development

### Backend

- Copy `backend/.env.example` to `backend/.env`
- Start local backend directly:

```bash
./scripts/start-backend.sh
```

- Or use Docker Compose:

```bash
docker compose up --build
```

### Frontend

- Copy `frontend/.env.example` to `frontend/.env.local`
- Start the Vite dev server:

```bash
cd frontend
npm install
npm run dev
```

### Local Telegram webhook

- Start `ngrok` via Compose if needed:

```bash
docker compose up -d ngrok
```

- Register the tunnel URL as Telegram webhook:

```bash
./scripts/sync-telegram-webhook.sh
```

## 2. Railway backend

Deploy the `backend` directory as the service root and use the existing `Dockerfile`.

### Required Railway variables

- `ENV=production`
- `JWT_SECRET=<strong-random-value>`
- `DATABASE_URL=<Railway Postgres URL>`
- `OPENAI_API_KEY=<your-openai-key>`
- `OPENAI_MODEL=gpt-4o-mini`
- `CORS_ORIGINS=https://<your-vercel-domain>`
- `TELEGRAM_BOT_TOKEN=<your-bot-token>`
- `TELEGRAM_BOT_USERNAME=<your-bot-username>`
- `TELEGRAM_WEBHOOK_SECRET=<strong-random-value>`

### Notes

- The backend now listens on `PORT` automatically, with `8000` as local fallback.
- `DATABASE_URL` values using `postgres://` or `postgresql://` are normalized automatically for async SQLAlchemy.
- Alembic still runs on boot by default. Set `RUN_MIGRATIONS=0` only if you want to manage migrations outside container startup.
- Railway healthcheck target should be:

```text
/api/health
```

- Use `GET /api/health/ready` in orchestration or smoke tests when you need to verify PostgreSQL connectivity (returns `503` if the database is down).

## 3. Vercel frontend

Set the Vercel project root directory to:

```text
frontend
```

### Vercel settings

- Build command: `npm run build`
- Output directory: `dist`

### Required Vercel variables

- `VITE_API_BASE_URL=https://<your-railway-backend>/api`

### Notes

- `frontend/vercel.json` provides SPA fallback rewrites for React Router.
- Local development still uses `frontend/.env.local`.

## 4. Production Telegram webhook

Once the Railway backend is live, register the stable public URL instead of ngrok:

```bash
WEBHOOK_PUBLIC_BASE_URL=https://<your-railway-backend> ./scripts/sync-telegram-webhook.sh
```

The webhook target becomes:

```text
https://<your-railway-backend>/api/telegram/webhook
```

## 5. Local vs production webhook rule

Telegram supports one active webhook per bot.

That means:

- if the bot points to Railway, local ngrok will not receive updates
- if the bot points to ngrok, Railway will not receive updates

Recommended options:

- use one bot for local and one bot for production, or
- switch webhook deliberately when testing locally

## 6. Final validation checklist

### Local

- `./scripts/start-backend.sh` works
- `npm run dev` in `frontend/` works
- login works from the browser
- diet generation works locally
- `./scripts/sync-telegram-webhook.sh` works with ngrok

### Production

- Railway service becomes healthy on `/api/health`
- Vercel frontend loads direct routes like `/dashboard` and `/diets/123`
- frontend can login against the Railway backend
- patient list and diet detail load correctly
- PDF download works
- Telegram binding link works
- Telegram webhook responds with `TELEGRAM_WEBHOOK_SECRET`
- Telegram can generate and approve a diet using the production backend
