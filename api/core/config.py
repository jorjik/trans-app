import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import Optional
from functools import lru_cache

log = logging.getLogger(__name__)

# Placeholder values that MUST be overridden in production
PLACEHOLDER_SECRET_KEY = "change-me-in-production-min-64-chars"
PLACEHOLDER_INTERNAL_SECRET = "change-me-bot-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    env: str = Field("development", alias="ENV")
    debug: bool = Field(False, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(["*"], alias="CORS_ORIGINS")

    # Security
    secret_key: str = Field(PLACEHOLDER_SECRET_KEY, alias="SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expire_seconds: int = 3600

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_webhook_secret: Optional[str] = Field(None, alias="BOT_WEBHOOK_SECRET")

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://transapp:password@localhost:5432/transapp",
        alias="DATABASE_URL",
    )
    db_pool_size: int = Field(10, alias="DATABASE_POOL_SIZE")
    db_max_overflow: int = Field(20, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    cache_ttl_short: int = Field(86_400, alias="CACHE_TTL_SHORT")  # 24h
    cache_ttl_long: int = Field(604_800, alias="CACHE_TTL_LONG")  # 7d

    # Translation providers
    deepl_api_key: Optional[str] = Field(None, alias="DEEPL_API_KEY")
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_TRANSLATE_API_KEY")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    default_engine: str = Field("google_free", alias="DEFAULT_TRANSLATION_ENGINE")

    # Quotas
    free_plan_chars: int = Field(50_000, alias="FREE_PLAN_CHARS")
    referral_bonus_chars: int = Field(10_000, alias="REFERRAL_BONUS_CHARS")

    # Internal
    bot_internal_secret: str = Field(PLACEHOLDER_INTERNAL_SECRET, alias="BOT_INTERNAL_SECRET")

    # Admin
    admin_tg_ids: list[int] = Field(default_factory=list, alias="ADMIN_TG_IDS")

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.env != "production":
            return self

        if self.secret_key in (PLACEHOLDER_SECRET_KEY, ""):
            log.warning("SECRET_KEY is still set to placeholder in production! Set a strong random value.")

        if self.bot_internal_secret in (PLACEHOLDER_INTERNAL_SECRET, ""):
            log.warning(
                "BOT_INTERNAL_SECRET is still set to placeholder in production! "
                "Set a strong random value via BOT_INTERNAL_SECRET env var."
            )

        if not self.bot_webhook_secret:
            log.warning("BOT_WEBHOOK_SECRET is not set in production! ")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
