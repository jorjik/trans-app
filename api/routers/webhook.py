"""
POST /webhook/telegram — приём апдейтов от Telegram Bot API.
POST /webhook/monobank — приём вебхуков от Monobank Acquiring API.
Используется в production.
"""

import hashlib
import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import validate_webhook_secret
from db.session import get_db
from models import PaymentIntent, User, BillingEvent
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


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> JSONResponse:
    """
    Принимает апдейты от Telegram.
    Секрет передаётся в заголовке X-Telegram-Bot-Api-Secret-Token.

    В текущей архитектуре бот работает как отдельный процесс (polling).
    Этот эндпоинт нужен для production webhook-режима.
    """
    if not validate_webhook_secret(x_telegram_bot_api_secret_token):
        log.warning("Webhook: invalid secret token")
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    try:
        update: dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid json"})

    update_id = update.get("update_id", "?")
    update_type = _detect_update_type(update)
    log.info("Webhook update received: id=%s type=%s", update_id, update_type)

    # TODO: передать апдейт боту через очередь (Redis pub/sub или Celery)
    # В MVP бот работает отдельно через polling — этот эндпоинт-заглушка

    return JSONResponse(status_code=200, content={"ok": True})


def _detect_update_type(update: dict) -> str:
    for key in ("message", "callback_query", "inline_query",
                "channel_post", "edited_message", "pre_checkout_query",
                "successful_payment"):
        if key in update:
            return key
    return "unknown"


# ── Monobank Webhook ──────────────────────────────────────────────────────────


@router.post("/monobank", include_in_schema=False)
async def handle_monobank_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Принимает вебхук от Monobank при изменении статуса счета."""
    if not settings.monobank_token:
        log.warning("Monobank token not configured")
        return {"error": "not_configured"}

    # Читаем сырое тело (нужно для верификации подписи)
    body_bytes = await request.body()
    x_sign = request.headers.get("X-Sign", "")

    # Верификация подписи ECDSA (опционально — только если библиотека установлена)
    try:
        from services.monobank import fetch_public_key, verify_webhook_signature
        pub_key = await fetch_public_key()
        if pub_key and x_sign:
            if not verify_webhook_signature(body_bytes, x_sign, pub_key):
                log.warning("Monobank webhook: invalid signature")
                return {"error": "invalid_signature"}
    except ImportError:
        log.info("Monobank webhook signature verification skipped (ecdsa not installed)")

    # Парсим тело
    try:
        data = json.loads(body_bytes)
    except json.JSONDecodeError:
        log.warning("Monobank webhook: invalid JSON")
        return {"error": "invalid_json"}

    invoice_id = data.get("invoiceId", "")
    status = data.get("status", "")

    if not invoice_id:
        log.warning("Monobank webhook: missing invoiceId")
        return {"error": "missing_invoice_id"}

    log.info("Monobank webhook: invoice=%s status=%s", invoice_id, status)

    # Обрабатываем только success
    if status != "success":
        return {"ok": True, "status": status}

    # Ищем PaymentIntent
    result = await db.execute(
        select(PaymentIntent).where(
            PaymentIntent.code == invoice_id,
            PaymentIntent.provider == "monobank",
        )
    )
    intent = result.scalar_one_or_none()
    if not intent:
        log.warning("Monobank payment intent not found: %s", invoice_id)
        return {"error": "intent_not_found"}

    if intent.status != "pending":
        log.info("Monobank intent %s already %s", invoice_id, intent.status)
        return {"ok": True, "status": "already_processed"}

    # Подтверждаем платёж
    intent.status = "paid"
    intent.external_id = data.get("reference", invoice_id)

    # Ищем пользователя
    user_result = await db.execute(
        select(User).where(User.id == intent.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        log.error("User %s not found for Monobank payment", intent.user_id)
        return {"error": "user_not_found"}

    # Записываем BillingEvent
    db.add(BillingEvent(
        user_id=user.id,
        provider="monobank",
        provider_charge_id=invoice_id,
        plan_id=intent.plan_id,
        amount=_get_amount_in_stars(data.get("amount", 0), data.get("ccy", 980)),
    ))

    # Апгрейдим план
    await upgrade_plan(db, user.id, intent.plan_id)
    await db.flush()

    log.info(
        "Monobank payment applied user=%s plan=%s invoice=%s",
        user.id, intent.plan_id, invoice_id,
    )

    # Уведомляем пользователя
    plan_name = intent.plan_id.capitalize()
    await _send_telegram_message(
        user.telegram_id,
        f"✅ <b>Monobank payment received!</b>\n\n"
        f"Plan: <b>{plan_name}</b> activated.\n"
        f"Thank you for your support! 🙏",
    )

    return {"ok": True, "status": "paid", "plan": intent.plan_id}


def _get_amount_in_stars(amount: int, ccy: int) -> int:
    """Конвертирует сумму из копеек/центов в условные единицы для BillingEvent."""
    # Monobank amount в минимальных единицах (копейки для UAH, центы для USD)
    # Просто возвращаем как есть, делим на 100
    return max(0, amount // 100)
