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

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_WEBHOOK_SECRET: str | None = None

    @property
    def is_production(self) -> bool:
        return self.ENV in {"production", "prod"}

    @model_validator(mode="after")
    def normalize_values(self) -> "Settings":
        self.ENV = (self.ENV or "development").strip().lower()
        self.CORS_ORIGINS = (self.CORS_ORIGINS or "*").strip() or "*"
        self.DATABASE_URL = normalize_async_database_url(self.DATABASE_URL)
        self.TELEGRAM_BOT_USERNAME = (self.TELEGRAM_BOT_USERNAME or "").strip()
        self.TELEGRAM_WEBHOOK_SECRET = (
            self.TELEGRAM_WEBHOOK_SECRET.strip()
            if isinstance(self.TELEGRAM_WEBHOOK_SECRET, str)
            and self.TELEGRAM_WEBHOOK_SECRET.strip()
            else None
        )
        if self.is_production and self.JWT_SECRET == "change-me":
            raise ValueError("JWT_SECRET must be configured in production")
        if self.is_production and not self.TELEGRAM_WEBHOOK_SECRET:
            raise ValueError(
                "TELEGRAM_WEBHOOK_SECRET must be configured in production"
            )
        return self


settings = Settings()
