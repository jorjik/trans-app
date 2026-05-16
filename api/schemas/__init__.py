"""Pydantic схемы для всех эндпоинтов."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


# ── Auth ───────────────────────────────────────────────────────────────────────

class TelegramAuthRequest(BaseModel):
    init_data: str


class UserBrief(BaseModel):
    id: int
    telegram_id_hash: str
    target_language: str
    plan: str
    chars_remaining: int


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserBrief


# ── User ───────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    target_language: str
    favorite_langs: list[str]
    preferred_engine: str
    plan: str
    chars_limit: int
    chars_used: int
    chars_remaining: int
    reset_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    target_language: Optional[str] = Field(None, min_length=2, max_length=10)
    favorite_langs: Optional[list[str]] = Field(None, max_length=10)
    preferred_engine: Optional[str] = Field(None, pattern="^(auto|google|deepl|openai)$")


# ── Translate ──────────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    target_lang: str = Field(..., min_length=2, max_length=10)
    source_lang: str = Field("auto", min_length=2, max_length=10)
    engine: str = Field("auto", pattern="^(auto|google|deepl|openai|google_free)$")


class TranslateResponse(BaseModel):
    translated_text: str
    source_lang_detected: str
    target_lang: str
    provider: str
    cached: bool
    char_count: int
    chars_remaining: int


# ── Chats ──────────────────────────────────────────────────────────────────────

class ChatConfigCreate(BaseModel):
    chat_username: Optional[str] = Field(None, min_length=3, max_length=128)
    chat_id: Optional[int] = None
    source_lang: str = Field("auto", min_length=2, max_length=10)
    target_lang: str = Field(..., min_length=2, max_length=10)

    @model_validator(mode="after")
    def check_chat_identity(self):
        if not self.chat_username and not self.chat_id:
            raise ValueError("Either chat_username or chat_id is required")
        return self


class ChatConfigUpdate(BaseModel):
    source_lang: Optional[str] = Field(None, min_length=2, max_length=10)
    target_lang: Optional[str] = Field(None, min_length=2, max_length=10)
    is_active: Optional[bool] = None


class ChatConfigResponse(BaseModel):
    id: int
    chat_id: int
    chat_title: Optional[str]
    chat_username: Optional[str]
    source_lang: str
    target_lang: str
    is_active: bool
    last_synced_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    items: list[ChatConfigResponse]
    total: int
    limit_reached: bool
    max_chats: int


class TranslatedMessage(BaseModel):
    message_id: int
    date: datetime
    original_text: str
    translated_text: str
    source_lang: str
    sender_name: Optional[str]


class ChatMessagesResponse(BaseModel):
    items: list[TranslatedMessage]
    total: int


# ── Stats ──────────────────────────────────────────────────────────────────────

class DailyStats(BaseModel):
    date: str
    chars: int


class LangStats(BaseModel):
    lang: str
    chars: int


class ProviderStats(BaseModel):
    google: int = 0
    deepl: int = 0
    openai: int = 0
    google_free: int = 0


class StatsResponse(BaseModel):
    period: str
    total_chars: int
    total_requests: int
    chars_by_day: list[DailyStats]
    top_languages: list[LangStats]
    providers_used: ProviderStats


# ── Billing ────────────────────────────────────────────────────────────────────

class PlanResponse(BaseModel):
    id: str
    name: str
    chars_per_month: int
    price_usd: float
    price_stars: int
    max_auto_chats: int
    features: list[str]

    model_config = {"from_attributes": True}


class PlansListResponse(BaseModel):
    plans: list[PlanResponse]


class CheckoutRequest(BaseModel):
    plan_id: str = Field(..., pattern="^(starter|pro|business)$")
    payment_method: str = Field("telegram_stars", pattern="^(telegram_stars|stripe)$")


class CheckoutResponse(BaseModel):
    invoice_url: str
    expires_at: datetime
