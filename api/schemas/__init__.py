"""Pydantic схемы запросов/ответов."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Auth ───────────────────────────────────────────────────────────────────────

class TelegramAuthRequest(BaseModel):
    init_data: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"
    is_new: bool = False


# ── User ───────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    ui_language: str = "en"
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
    ui_language: Optional[str] = Field(None, min_length=2, max_length=10)
    target_language: Optional[str] = Field(None, min_length=2, max_length=10)
    favorite_langs: Optional[list[str]] = Field(None, max_length=10)
    preferred_engine: Optional[str] = Field(
        None, pattern="^(auto|google|deepl|openai|google_free)$"
    )


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
    chat_username: Optional[str] = None
    chat_id: Optional[int] = None
    source_lang: str = "auto"
    target_lang: str = Field(..., min_length=2, max_length=10)

    @field_validator("chat_username", mode="before")
    @classmethod
    def strip_at(cls, v):
        return v[1:] if v and v.startswith("@") else v


class ChatConfigUpdate(BaseModel):
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    is_active: Optional[bool] = None


class ChatConfigResponse(BaseModel):
    id: int
    chat_id: Optional[int]
    chat_title: Optional[str]
    chat_username: Optional[str]
    source_lang: str
    target_lang: str
    is_active: bool
    last_synced_at: Optional[datetime]
    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    items: list[ChatConfigResponse]
    total: int
    limit_reached: bool
    max_chats: int


# ── Stats ──────────────────────────────────────────────────────────────────────

class DayStats(BaseModel):
    date: str
    chars: int


class LangStats(BaseModel):
    lang: str
    chars: int


class StatsResponse(BaseModel):
    period: str
    total_chars: int
    total_requests: int
    chars_by_day: list[DayStats]
    top_languages: list[LangStats]
    providers_used: dict


# ── Billing ────────────────────────────────────────────────────────────────────

class PlanResponse(BaseModel):
    id: str
    name: str
    chars_per_month: int
    price_usd: Optional[float]
    price_stars: Optional[int]
    max_auto_chats: int
    features: list[str]


class PlansListResponse(BaseModel):
    plans: list[PlanResponse]
    current_plan: str


class CheckoutRequest(BaseModel):
    plan_id: str
    payment_method: str = Field(..., pattern="^(telegram_stars|stripe|yookassa)$")


class CheckoutResponse(BaseModel):
    invoice_url: str
    expires_at: datetime


class StarsInternalPayment(BaseModel):
    telegram_id: int
    plan_id: str
    telegram_payment_charge_id: str
    total_amount: int
