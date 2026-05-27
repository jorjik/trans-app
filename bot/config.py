import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator, computed_field
from typing import Optional

log = logging.getLogger(__name__)

PLACEHOLDER_INTERNAL_SECRET = "change-me-bot-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")
    mini_app_url: str = Field("https://example.com/miniapp", alias="MINI_APP_URL")
    bot_webhook_secret: Optional[str] = Field(None, alias="BOT_WEBHOOK_SECRET")

    # Redis (опциональный для MVP)
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    use_redis: bool = Field(False, alias="USE_REDIS")

    # Translation providers
    deepl_api_key: Optional[str] = Field(None, alias="DEEPL_API_KEY")
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_TRANSLATE_API_KEY")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    default_engine: str = Field("google_free", alias="DEFAULT_TRANSLATION_ENGINE")

    # Quotas
    free_plan_chars: int = Field(25_000, alias="FREE_PLAN_CHARS")
    referral_bonus_chars: int = Field(10_000, alias="REFERRAL_BONUS_CHARS")

    # Backend API (синхронизация оплаты Stars + ui_language)
    api_url: Optional[str] = Field(None, alias="BACKEND_API_URL")
    bot_internal_secret: str = Field(PLACEHOLDER_INTERNAL_SECRET, alias="BOT_INTERNAL_SECRET")

    # App
    env: str = Field("development", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    # str — pydantic-settings парсит list[int] из .env только как JSON;
    # comma-separated значения (123,456) дают JSONDecodeError.
    admin_tg_ids_raw: str = Field(default="", alias="ADMIN_TG_IDS")

    # Magic numbers (вынесены из хендлеров)
    max_result_length: int = Field(4096, alias="MAX_RESULT_LENGTH")
    max_inline_query_len: int = Field(1000, alias="MAX_INLINE_QUERY_LEN")
    min_inline_query_len: int = Field(2, alias="MIN_INLINE_QUERY_LEN")
    translate_chunk_size: int = Field(4500, alias="TRANSLATE_CHUNK_SIZE")
    max_translation_cache: int = Field(500, alias="MAX_TRANSLATION_CACHE")
    translation_cache_ttl: int = Field(86_400, alias="TRANSLATION_CACHE_TTL")  # 24h

    # Rate limiting
    max_requests_per_minute: int = Field(30, alias="MAX_REQUESTS_PER_MINUTE")
    max_translate_per_minute: int = Field(15, alias="MAX_TRANSLATE_PER_MINUTE")

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.env != "production":
            return self
        if self.bot_internal_secret in (PLACEHOLDER_INTERNAL_SECRET, ""):
            log.warning(
                "BOT_INTERNAL_SECRET is still set to placeholder in production! "
                "Set a strong random value via BOT_INTERNAL_SECRET env var."
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_tg_ids(self) -> list[int]:
        raw = self.admin_tg_ids_raw.strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            parsed = json.loads(raw)
            return [int(x) for x in parsed]
        return [int(x.strip()) for x in raw.split(",") if x.strip()]


settings = Settings()
