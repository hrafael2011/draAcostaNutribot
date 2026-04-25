import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401 — registers all ORM models on Base.metadata

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

# Quieter client libraries; app loggers still emit ERROR/WARNING as needed.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

app = FastAPI(title=settings.APP_NAME)

_cors = settings.CORS_ORIGINS.strip()
_allow_origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
_allow_credentials = _allow_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def create_tables() -> None:
    """Create missing tables only in local development.

    Deployed environments run Alembic before Uvicorn starts; running create_all
    afterwards can race or conflict with versioned migrations.
    """
    if settings.is_production:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"status": "ok", "service": "diet-telegram-agent"}


app.include_router(api_router, prefix="/api")
