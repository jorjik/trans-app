"""Обработчики ошибок."""

import logging
from aiogram import Router
from aiogram.types import ErrorEvent

from services.storage import get_user
from utils.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    logger.error(
        "Unhandled error: %s | Update: %s",
        event.exception,
        event.update,
        exc_info=event.exception,
    )
    # Пытаемся уведомить пользователя
    try:
        if event.update.message:
            user = get_user(event.update.message.from_user.id)
            await event.update.message.answer(t("error_generic", user.ui_language))
    except Exception:
        pass
