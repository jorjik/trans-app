"""Internal API — endpoints для взаимодействия бота с API (защищены общим секретом)."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from core.config import settings
from db.session import get_db
from models import User
from services.quota import get_or_create_quota
from core.security import hash_telegram_id

log = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if x_bot_secret != settings.bot_internal_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


# Канонические коды UI-языков
_UI_LANGS = ("en", "ru", "uk", "de", "fr", "es", "pl", "it", "pt", "tr")


class SyncUiLangRequest(BaseModel):
    telegram_id: int
    ui_language: str


@router.post("/sync-ui-lang", dependencies=[Depends(verify_bot_secret)])
async def sync_ui_lang(
    body: SyncUiLangRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Синхронизирует ui_language из бота в БД API."""
    user = await _get_or_create_user(db, body.telegram_id)

    if body.ui_language not in _UI_LANGS:
        log.warning("sync-ui-lang: invalid language %s", body.ui_language)
        return {"status": "invalid_lang"}

    user.ui_language = body.ui_language
    await db.commit()
    log.info("sync-ui-lang: updated user=%s lang=%s", user.id, body.ui_language)
    return {"status": "ok"}


# ── Internal: user settings for bot persistence ────────────────────────────────

class UserSettingsRequest(BaseModel):
    telegram_id: int


class UserSettingsResponse(BaseModel):
    target_language: str
    ui_language: str
    favorite_langs: list[str]
    plan: str
    chars_limit: int
    chars_used: int
    chars_remaining: int
    reset_at: Optional[str] = None


class DeductCharsRequest(BaseModel):
    telegram_id: int
    char_count: int


class UpdateSettingsRequest(BaseModel):
    telegram_id: int
    target_language: Optional[str] = None
    ui_language: Optional[str] = None
    favorite_langs: Optional[list[str]] = None


async def _get_or_create_user(db: AsyncSession, telegram_id: int) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=telegram_id,
            telegram_id_hash=hash_telegram_id(telegram_id),
        )
        db.add(user)
        await db.flush()
        log.info("auto-created user telegram_id=%s id=%s", telegram_id, user.id)
    return user


@router.post(
    "/user/settings",
    dependencies=[Depends(verify_bot_secret)],
    response_model=UserSettingsResponse,
)
async def get_user_settings(
    body: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Возвращает настройки пользователя по telegram_id для бота."""
    user = await _get_or_create_user(db, body.telegram_id)

    quota = await get_or_create_quota(db, user.id)

    return UserSettingsResponse(
        target_language=user.target_language or "en",
        ui_language=user.ui_language or "",
        favorite_langs=user.favorite_langs or ["en", "de", "fr"],
        plan=quota.plan,
        chars_limit=quota.chars_limit,
        chars_used=quota.chars_used,
        chars_remaining=quota.chars_remaining,
        reset_at=quota.reset_at.isoformat() if quota.reset_at else None,
    )


@router.post(
    "/user/deduct-chars",
    dependencies=[Depends(verify_bot_secret)],
    response_model=UserSettingsResponse,
)
async def deduct_user_chars(
    body: DeductCharsRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Списывает символы пользователя (вызов из бота после перевода)."""
    user = await _get_or_create_user(db, body.telegram_id)

    from services.quota import deduct_chars as quota_deduct
    quota = await quota_deduct(db, user.id, body.char_count)

    return UserSettingsResponse(
        target_language=user.target_language or "en",
        ui_language=user.ui_language or "",
        favorite_langs=user.favorite_langs or ["en", "de", "fr"],
        plan=quota.plan,
        chars_limit=quota.chars_limit,
        chars_used=quota.chars_used,
        chars_remaining=quota.chars_remaining,
        reset_at=quota.reset_at.isoformat() if quota.reset_at else None,
    )


@router.post(
    "/user/update-settings",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def update_user_settings(
    body: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Обновляет настройки пользователя из бота."""
    user = await _get_or_create_user(db, body.telegram_id)

    if body.target_language is not None:
        user.target_language = body.target_language
    if body.ui_language is not None:
        if body.ui_language in _UI_LANGS:
            user.ui_language = body.ui_language
    if body.favorite_langs is not None:
        user.favorite_langs = body.favorite_langs[:10]

    await db.commit()
    return {"status": "ok"}


# ── Internal: payment endpoints for bot (Ko-fi, PayPal) ───────────────────────

class PaymentIntentRequest(BaseModel):
    telegram_id: int
    plan_id: str
    payment_method: str  # "kofi" or "paypal"


class PayPalCaptureRequest(BaseModel):
    telegram_id: int
    order_id: str


class PayPalStatusRequest(BaseModel):
    telegram_id: int
    order_id: str


@router.post(
    "/payment/intent",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def internal_create_payment_intent(
    body: PaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Создаёт платёжное намерение (Ko-fi) от имени пользователя по telegram_id."""
    from datetime import datetime, timezone, timedelta
    from models import PaymentIntent, User
    from services.kofi import amount_for_plan as kofi_amount_for_plan
    from api.routers.kofi import generate_kofi_code

    user = await _get_or_create_user(db, body.telegram_id)

    if body.plan_id not in ("starter", "pro", "business"):
        return {"error": "invalid_plan"}

    plan_stars = {"starter": 250, "pro": 750, "business": 2500}
    price_stars = plan_stars.get(body.plan_id, 250)

    if body.payment_method == "kofi":
        code = generate_kofi_code(user.id, body.plan_id)
        amount = kofi_amount_for_plan(price_stars, settings.kofi_amount_per_star)
        db.add(PaymentIntent(
            user_id=user.id,
            provider="kofi",
            plan_id=body.plan_id,
            code=code,
            amount=amount,
            currency=settings.kofi_currency,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
        await db.flush()
        return {
            "provider": "kofi",
            "code": code,
            "amount": amount,
            "currency": settings.kofi_currency,
            "page_url": settings.kofi_page_url or "https://ko-fi.com",
        }

    return {"error": "unsupported_payment_method"}


@router.post(
    "/payment/paypal-create",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def internal_paypal_create_order(
    body: PaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Создаёт PayPal заказ от имени пользователя по telegram_id."""
    from datetime import datetime, timezone, timedelta
    from models import PaymentIntent, User
    from services.kofi import amount_for_plan as kofi_amount_for_plan
    from services.paypal import PayPalClient

    user = await _get_or_create_user(db, body.telegram_id)

    if body.plan_id not in ("starter", "pro", "business"):
        return {"error": "invalid_plan"}

    plan_stars = {"starter": 250, "pro": 750, "business": 2500}
    price_stars = plan_stars.get(body.plan_id, 250)

    amount = kofi_amount_for_plan(price_stars, settings.paypal_amount_per_star)
    reference_id = f"user_{user.id}_plan_{body.plan_id}"

    client = PayPalClient()
    order = await client.create_order(
        amount=amount,
        currency=settings.paypal_currency,
        reference_id=reference_id,
    )

    if not order:
        return {"error": "paypal_error", "detail": client.last_error or "Failed to create order"}

    order_id = order["id"]
    approval_url = next(
        (link["href"] for link in order.get("links", []) if link.get("rel") == "approve"),
        None,
    )

    db.add(PaymentIntent(
        user_id=user.id,
        provider="paypal",
        plan_id=body.plan_id,
        code=order_id,
        amount=amount,
        currency=settings.paypal_currency,
        external_id=order_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=3),
    ))
    await db.flush()

    return {
        "provider": "paypal",
        "order_id": order_id,
        "approval_url": approval_url or "",
        "amount": amount,
        "currency": settings.paypal_currency,
    }


@router.post(
    "/payment/paypal-capture/{order_id}",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def internal_paypal_capture_order(
    order_id: str,
    body: PayPalCaptureRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Захватывает PayPal заказ и активирует тариф."""
    from models import PaymentIntent, BillingEvent, User
    from services.paypal import PayPalClient
    from services.quota import upgrade_plan

    user = await _get_or_create_user(db, body.telegram_id)

    result = await db.execute(
        select(PaymentIntent).where(
            PaymentIntent.code == order_id,
            PaymentIntent.user_id == user.id,
            PaymentIntent.provider == "paypal",
        )
    )
    intent = result.scalar_one_or_none()
    if not intent:
        return {"error": "intent_not_found"}

    if intent.status == "paid":
        return {"status": "already_paid", "plan": intent.plan_id}

    client = PayPalClient()
    capture = await client.capture_order(order_id)
    if not capture:
        return {"error": "paypal_error", "detail": client.last_error or "Failed to capture"}

    if capture.get("status") != "COMPLETED":
        return {"status": capture.get("status", "unknown"), "order_id": order_id}

    capture_id = ""
    purchase_units = capture.get("purchase_units") or []
    if purchase_units:
        captures = purchase_units[0].get("payments", {}).get("captures") or []
        if captures:
            capture_id = captures[0].get("id", "")

    intent.status = "paid"
    intent.external_id = capture_id

    db.add(BillingEvent(
        user_id=user.id,
        provider="paypal",
        provider_charge_id=capture_id or order_id,
        plan_id=intent.plan_id,
        amount=0,
    ))

    await upgrade_plan(db, user.id, intent.plan_id)
    await db.flush()

    return {"status": "paid", "plan": intent.plan_id}


@router.post(
    "/payment/paypal-status/{order_id}",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def internal_paypal_order_status(
    order_id: str,
    body: PayPalStatusRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Проверяет статус PayPal заказа."""
    from services.paypal import PayPalClient

    client = PayPalClient()
    order = await client.get_order(order_id)
    if not order:
        return {"error": "paypal_error", "detail": client.last_error or "Failed to get order"}

    return {"status": order.get("status", "unknown"), "order_id": order_id}
