from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
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
    free_plan_chars: int = Field(50_000, alias="FREE_PLAN_CHARS")
    referral_bonus_chars: int = Field(10_000, alias="REFERRAL_BONUS_CHARS")

    # Backend API (для будущей интеграции)
    api_url: Optional[str] = Field(None, alias="BACKEND_API_URL")

    # App
    env: str = Field("development", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    # str — pydantic-settings парсит list[int] из .env только как JSON;
    # comma-separated значения (123,456) дают JSONDecodeError.
    admin_tg_ids_raw: str = Field(default="", alias="ADMIN_TG_IDS")

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
