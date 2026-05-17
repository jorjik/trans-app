"""
POST /webhook/telegram — приём апдейтов от Telegram Bot API.
Используется в production (вместо polling).
В dev-режиме бот работает через polling напрямую.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from core.security import validate_webhook_secret

log = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


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
