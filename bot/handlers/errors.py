"""Обработчики ошибок."""

import logging
from aiogram import Router
from aiogram.types import ErrorEvent

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
            await event.update.message.answer(
                "❌ Что-то пошло не так. Попробуй ещё раз."
            )
    except Exception:
        pass
