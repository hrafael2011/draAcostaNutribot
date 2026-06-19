from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_async_database_url(url: str) -> str:
    value = (url or "").strip()
    if value.startswith("postgres://"):
        value = f"postgresql://{value[len('postgres://'):]}"
    if value.startswith("postgresql://"):
        return f"postgresql+asyncpg://{value[len('postgresql://'):]}"
    return value


def to_sync_database_url(url: str) -> str:
    value = normalize_async_database_url(url)
    if value.startswith("postgresql+asyncpg://"):
        return f"postgresql://{value[len('postgresql+asyncpg://'):]}"
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # App
    APP_NAME: str = "Diet Telegram Agent"
    APP_URL: str = ""
    ENV: str = "development"
    PORT: int = 8000
    CORS_ORIGINS: str = "*"

    # Security
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # DB
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/diet_agent"
    )

    # OpenAI / DeepSeek (OpenAI-compatible)
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Telegram (legacy — only the feature flag remains)
    TELEGRAM_ENABLED: bool = True

    # Gmail API
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    GMAIL_FROM_EMAIL: str = ""

    # Reminders
    REMINDER_ENABLED: bool = False
    REMINDER_DAYS: int = 30
    REMINDER_INTERVAL_MINUTES: int = 5

    @property
    def is_production(self) -> bool:
        return self.ENV in {"production", "prod"}

    @model_validator(mode="after")
    def normalize_values(self) -> "Settings":
        self.ENV = (self.ENV or "development").strip().lower()
        self.CORS_ORIGINS = (self.CORS_ORIGINS or "*").strip() or "*"
        self.DATABASE_URL = normalize_async_database_url(self.DATABASE_URL)
        if self.is_production and self.JWT_SECRET == "change-me":
            raise ValueError("JWT_SECRET must be configured in production")
        if self.is_production and self.CORS_ORIGINS.strip() == "*":
            import logging
            logging.getLogger(__name__).warning(
                "CORS_ORIGINS='*' in production — restrict to specific origins via CORS_ORIGINS env var"
            )
        return self


settings = Settings()
