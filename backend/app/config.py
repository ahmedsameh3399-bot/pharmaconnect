"""Centralized runtime configuration.

All settings come from environment variables. Defaults exist only for values
that are safe in local development (e.g. CORS origins). Secrets have no
defaults so the app refuses to start if they're missing in production.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://pharma:pharma_dev_password@db:5432/pharma_connect",
        alias="DATABASE_URL",
    )

    # --- JWT ---
    jwt_secret: str = Field(default="dev-only-secret-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # --- CORS ---
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    # --- Email (optional in dev) ---
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="no-reply@pharma-connect.local", alias="SMTP_FROM")
    smtp_tls: bool = Field(default=True, alias="SMTP_TLS")

    # --- Claude API (optional; chatbot disabled when missing) ---
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-haiku-4-5", alias="CLAUDE_MODEL")
    chatbot_daily_request_limit: int = Field(default=50, alias="CHATBOT_DAILY_REQUEST_LIMIT")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chatbot_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
