"""
Rate limiting middleware.
MVP: in-memory с cachetools.TTLCache.
"""

import time
import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Кэш: user_id → список timestamp'ов запросов
_rate_cache: TTLCache = TTLCache(maxsize=10_000, ttl=60)

MAX_REQUESTS_PER_MINUTE = 30  # запросов/минуту на пользователя
MAX_TRANSLATE_PER_MINUTE = 15  # переводов/минуту на пользователя


class ThrottleMiddleware(BaseMiddleware):
    """Общий rate limiting для всех апдейтов."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        uid = user.id
        now = time.time()

        if uid not in _rate_cache:
            _rate_cache[uid] = []

        # Оставляем только запросы за последнюю минуту
        _rate_cache[uid] = [t for t in _rate_cache[uid] if now - t < 60]

        if len(_rate_cache[uid]) >= MAX_REQUESTS_PER_MINUTE:
            logger.warning("Rate limit hit for user %s", uid)
            if isinstance(event, Message):
                await event.answer(
                    "⏳ Слишком много запросов. Подожди немного.",
                    disable_notification=True,
                )
            return  # не вызываем handler

        _rate_cache[uid].append(now)
        return await handler(event, data)
