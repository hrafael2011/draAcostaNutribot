"""Railway TCP proxy DB URLs require sslmode for drivers."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, ensure_railway_tcp_proxy_ssl


def test_ensure_railway_tcp_proxy_ssl_appends_sslmode() -> None:
    base = "postgresql+asyncpg://u:p@db-foo.proxy.rlwy.net:12345/railway"
    out = ensure_railway_tcp_proxy_ssl(base)
    assert "sslmode=require" in out
    assert out.startswith("postgresql+asyncpg://")


def test_ensure_railway_tcp_proxy_ssl_idempotent() -> None:
    base = "postgresql://u:p@x.proxy.rlwy.net:1/db?sslmode=require"
    assert ensure_railway_tcp_proxy_ssl(base) == base


def test_settings_applies_ssl_for_proxy_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    url = "postgresql+asyncpg://u:p@db.proxy.rlwy.net:1111/railway"
    s = Settings(
        ENV="development",
        JWT_SECRET="x" * 64,
        TELEGRAM_WEBHOOK_SECRET="y" * 32,
        DATABASE_URL=url,
    )
    assert "proxy.rlwy.net" in s.DATABASE_URL
    assert "sslmode=require" in s.DATABASE_URL


def test_production_still_requires_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(
            ENV="production",
            JWT_SECRET="change-me",
            TELEGRAM_WEBHOOK_SECRET="secret",
            DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        )
