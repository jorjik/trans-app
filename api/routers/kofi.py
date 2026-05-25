"""Ko-fi вебхук — приём платежей от Ko-fi."""

import json
import logging
import secrets
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.session import get_db
from models import PaymentIntent, User, BillingEvent
from services.kofi import (
    extract_kofi_code,
    parse_kofi_webhook_payload,
)
from services.quota import upgrade_plan

log = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

TELEGRAM_API = "https://api.telegram.org"


async def _send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    """Отправляет сообщение пользователю через Bot API."""
    if not settings.bot_token:
        log.warning("BOT_TOKEN not set — cannot notify user %s", chat_id)
        return False
    url = f"{TELEGRAM_API}/bot{settings.bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            data = resp.json()
            if not data.get("ok"):
                log.warning("Telegram notify failed: %s", data.get("description"))
                return False
            return True
    except Exception:
        log.exception("Failed to send Telegram notification to %s", chat_id)
        return False


@router.post("/kofi", include_in_schema=False)
async def handle_kofi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Принимает вебхук от Ko-fi после успешного платежа."""
    if not settings.kofi_verification_token:
        log.warning("KOFI_VERIFICATION_TOKEN not configured")
        return {"ok": False, "error": "not_configured"}

    # Читаем payload
    try:
        body = await request.json()
    except Exception:
        # Ko-fi может отправить form-data
        form = await request.form()
        body = dict(form) if form else {}

    try:
        payment = parse_kofi_webhook_payload(body)
    except (json.JSONDecodeError, ValueError) as e:
        log.warning("Invalid Ko-fi payload: %s", e)
        return {"ok": False, "error": "invalid_payload"}

    # Верификация
    if payment.verification_token != settings.kofi_verification_token:
        log.warning("Ko-fi webhook invalid token: %s", payment.verification_token)
        return {"ok": False, "error": "invalid_token"}

    # Извлекаем код платежа из сообщения
    code = extract_kofi_code(payment.message)
    if not code:
        log.warning("Ko-fi payment without code: %s", payment.provider_payment_id)
        return {"ok": False, "error": "no_payment_code"}

    # Ищем PaymentIntent по коду
    result = await db.execute(
        select(PaymentIntent).where(PaymentIntent.code == code)
    )
    intent = result.scalar_one_or_none()
    if not intent:
        log.warning("Ko-fi payment code not found: %s", code)
        return {"ok": False, "error": "intent_not_found"}

    if intent.status != "pending":
        log.info("Ko-fi intent %s already %s", code, intent.status)
        return {"ok": True, "status": "already_processed"}

    # Подтверждаем платёж
    intent.status = "paid"
    intent.external_id = payment.provider_payment_id

    # Ищем пользователя
    user_result = await db.execute(
        select(User).where(User.id == intent.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        log.error("User %s not found for Ko-fi payment", intent.user_id)
        return {"ok": False, "error": "user_not_found"}

    # Записываем BillingEvent
    db.add(BillingEvent(
        user_id=user.id,
        provider="kofi",
        provider_charge_id=payment.provider_payment_id,
        plan_id=intent.plan_id,
        amount=0,
    ))

    # Апгрейдим план
    await upgrade_plan(db, user.id, intent.plan_id)
    await db.flush()

    log.info(
        "Ko-fi payment applied user=%s plan=%s tx=%s",
        user.id, intent.plan_id, payment.provider_payment_id,
    )

    # Уведомляем пользователя
    plan_name = intent.plan_id.capitalize()
    await _send_telegram_message(
        user.telegram_id,
        f"✅ <b>Ko-fi payment received!</b>\n\n"
        f"Plan: <b>{plan_name}</b> activated.\n"
        f"Thank you for your support! 🙏",
    )

    return {"ok": True, "status": "paid", "plan": intent.plan_id}


def generate_kofi_code(user_id: int, plan_id: str) -> str:
    """Генерирует уникальный код для отслеживания платежа Ko-fi."""
    rand = secrets.token_hex(4).upper()
    return f"KF-{user_id}-{plan_id.upper()}-{rand}"
