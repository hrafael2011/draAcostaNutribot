from app.core.config import normalize_async_database_url, to_sync_database_url


def test_normalize_async_database_url_accepts_postgres_scheme():
    assert normalize_async_database_url(
        "postgres://user:pass@db.example.com:5432/diet_agent"
    ) == "postgresql+asyncpg://user:pass@db.example.com:5432/diet_agent"


def test_normalize_async_database_url_accepts_postgresql_scheme():
    assert normalize_async_database_url(
        "postgresql://user:pass@db.example.com:5432/diet_agent?sslmode=require"
    ) == (
        "postgresql+asyncpg://user:pass@db.example.com:5432/"
        "diet_agent?sslmode=require"
    )


def test_to_sync_database_url_removes_asyncpg_driver():
    assert to_sync_database_url(
        "postgresql+asyncpg://user:pass@db.example.com:5432/diet_agent"
    ) == "postgresql://user:pass@db.example.com:5432/diet_agent"
