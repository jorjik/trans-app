"""Telegram Stars, Ko-fi, PayPal — счета и активация тарифов."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
from aiogram import Bot
from aiogram.types import LabeledPrice, Message

from config import settings
from services.api_client import _bot_secret_headers, _api_url

log = logging.getLogger(__name__)

PAYLOAD_PREFIX = "pay"


@dataclass(frozen=True)
class BillablePlan:
    id: str
    name: str
    chars_limit: int
    stars: int


# Звёздные тарифы для Telegram Stars инвойсов.
# Лимиты символов дублируют api/services/constants.py (единый источник правды).
# При изменении тарифов — обновлять в обоих местах.
BILLABLE_PLANS: dict[str, BillablePlan] = {
    "starter": BillablePlan("starter", "Starter", 500_000, 250),
    "pro": BillablePlan("pro", "Pro", 2_000_000, 750),
    "business": BillablePlan("business", "Business", 10_000_000, 2500),
}

# PLAN_LIMITS для обратной совместимости; storage.py теперь использует API
PLAN_LIMITS = {p.id: p.chars_limit for p in BILLABLE_PLANS.values()}
PLAN_LIMITS["free"] = 25_000


def build_payload(plan_id: str, telegram_id: int) -> str:
    return f"{PAYLOAD_PREFIX}:{plan_id}:{telegram_id}"


def parse_payload(payload: str) -> tuple[str, int] | None:
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != PAYLOAD_PREFIX:
        return None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None


def get_plan(plan_id: str) -> BillablePlan | None:
    return BILLABLE_PLANS.get(plan_id)


async def start_checkout(message: Message, plan_id: str) -> None:
    """Отправляет Stars-invoice в чат пользователя."""
    plan = get_plan(plan_id)
    if not plan:
        await message.answer("❌ Неизвестный тариф.")
        return

    await send_stars_invoice(
        message.bot,
        message.chat.id,
        message.from_user.id,
        plan_id,
    )


async def send_stars_invoice(
    bot: Bot,
    chat_id: int,
    telegram_id: int,
    plan_id: str,
) -> Message:
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Unknown plan: {plan_id}")

    return await bot.send_invoice(
        chat_id=chat_id,
        title=f"TransApp {plan.name}",
        description=f"{plan.chars_limit:,} символов в месяц",
        payload=build_payload(plan_id, telegram_id),
        currency="XTR",
        prices=[LabeledPrice(label=plan.name, amount=plan.stars)],
        provider_token="",
    )


async def notify_api_stars_paid(
    *,
    telegram_id: int,
    plan_id: str,
    charge_id: str,
    total_amount: int,
) -> bool:
    """Синхронизирует оплату с backend API (если настроен BACKEND_API_URL)."""
    if not settings.api_url or not settings.bot_webhook_secret:
        return False

    url = f"{settings.api_url.rstrip('/')}/billing/internal/stars"
    headers = {"X-Billing-Secret": settings.bot_webhook_secret}
    body = {
        "telegram_id": telegram_id,
        "plan_id": plan_id,
        "telegram_payment_charge_id": charge_id,
        "total_amount": total_amount,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    log.info("API synced Stars payment tg=%s plan=%s", telegram_id, plan_id)
                    return True
                text = await resp.text()
                log.warning("API Stars sync failed status=%s body=%s", resp.status, text[:200])
    except Exception:
        log.exception("API Stars sync error tg=%s", telegram_id)

    return False


# ── Ko-fi (через internal API) ────────────────────────────────────────────────

# ── Monobank (через internal API) ─────────────────────────────────────────────

async def create_monobank_intent(telegram_id: int, plan_id: str) -> dict[str, Any] | None:
    """Создаёт платёжное намерение Monobank через internal API."""
    if not settings.api_url:
        return None

    url = _api_url("/internal/payment/intent")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"telegram_id": telegram_id, "plan_id": plan_id, "payment_method": "monobank"},
                headers=_bot_secret_headers(),
                timeout=15,
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                log.warning("API monobank intent failed status=%s", resp.status)
    except Exception:
        log.exception("API monobank intent error")
    return None


async def create_kofi_intent(telegram_id: int, plan_id: str) -> dict[str, Any] | None:
    """Создаёт платёжное намерение Ko-fi через internal API."""
    if not settings.api_url:
        return None

    url = _api_url("/internal/payment/intent")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"telegram_id": telegram_id, "plan_id": plan_id, "payment_method": "kofi"},
                headers=_bot_secret_headers(),
                timeout=15,
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                log.warning("API kofi intent failed status=%s", resp.status)
    except Exception:
        log.exception("API kofi intent error")
    return None


# ── PayPal (через internal API) ────────────────────────────────────────────────

async def create_paypal_order(telegram_id: int, plan_id: str) -> dict[str, Any] | None:
    if not settings.api_url:
        return None

    url = _api_url("/internal/payment/paypal-create")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"telegram_id": telegram_id, "plan_id": plan_id, "payment_method": "paypal"},
                headers=_bot_secret_headers(),
                timeout=15,
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                log.warning("API paypal create order failed status=%s", resp.status)
    except Exception:
        log.exception("API paypal create order error")
    return None


async def capture_paypal_order(telegram_id: int, order_id: str) -> dict[str, Any] | None:
    if not settings.api_url:
        return None

    url = _api_url(f"/internal/payment/paypal-capture/{order_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"telegram_id": telegram_id, "order_id": order_id},
                headers=_bot_secret_headers(),
                timeout=15,
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                log.warning("API paypal capture failed status=%s", resp.status)
    except Exception:
        log.exception("API paypal capture error")
    return None


async def get_paypal_order_status(telegram_id: int, order_id: str) -> dict[str, Any] | None:
    if not settings.api_url:
        return None

    url = _api_url(f"/internal/payment/paypal-status/{order_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"telegram_id": telegram_id, "order_id": order_id},
                headers=_bot_secret_headers(),
                timeout=10,
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                log.warning("API paypal status failed status=%s", resp.status)
    except Exception:
        log.exception("API paypal status error")
    return None
