"""Telegram Stars — создание invoice link через Bot API."""

import json
import logging

import httpx

from core.config import settings
from core.errors import AppError
from services.billing_plans import PLAN_CATALOG, build_invoice_payload

log = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


async def create_stars_invoice_link(*, plan_id: str, telegram_id: int) -> str:
    plan = PLAN_CATALOG.get(plan_id)
    if not plan or plan.price_stars <= 0:
        raise AppError(
            status_code=422,
            error="invalid_plan",
            message=f"Plan cannot be purchased with Stars: {plan_id}",
        )

    payload = build_invoice_payload(plan_id, telegram_id)
    title = f"TransApp {plan.name}"
    description = (
        f"{plan.chars_per_month:,} символов в месяц. "
        f"Тариф {plan.name}."
    )

    body = {
        "title": title,
        "description": description,
        "payload": payload,
        "currency": "XTR",
        "prices": json.dumps([{"label": plan.name, "amount": plan.price_stars}]),
    }

    url = f"{TELEGRAM_API}/bot{settings.bot_token}/createInvoiceLink"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(url, data=body)

    data = response.json()
    if not data.get("ok"):
        log.error("createInvoiceLink failed: %s", data)
        raise AppError(
            status_code=502,
            error="telegram_invoice_failed",
            message=data.get("description", "Failed to create Stars invoice"),
        )

    invoice_url = data["result"]
    log.info("Stars invoice link created plan=%s tg_id=%s", plan_id, telegram_id)
    return invoice_url
