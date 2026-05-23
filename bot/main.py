"""
TransApp Bot — точка входа.

Запуск:
  python main.py

Режим: polling (для локальной разработки).
Webhook настраивается отдельно (infra/nginx) для production.
"""

import asyncio
import logging
import sys
from typing import Any, Callable, Awaitable

import structlog
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, CallbackQuery

from config import settings
from handlers import start, translate, inline, errors, billing
from middlewares.throttle import ThrottleMiddleware
from services.cache import close_redis
from services.api_client import close_session


# Временный middleware для диагностики callback_query
log_debug = logging.getLogger("callback_debug")


class CallbackDebugMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            log_debug.warning(
                "CALLBACK DEBUG: user=%s data=%s message_id=%s",
                event.from_user.id,
                event.data,
                event.message.message_id if event.message else None,
            )
        return await handler(event, data)


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.dev.ConsoleRenderer() if settings.env == "development"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format="%(message)s",
    )


async def main() -> None:
    setup_logging()
    logger = structlog.get_logger()

    logger.info("Starting TransApp Bot", env=settings.env)

    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Диспетчер
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(ThrottleMiddleware())
    dp.callback_query.middleware(ThrottleMiddleware())
    dp.callback_query.middleware(CallbackDebugMiddleware())

    # Роутеры (порядок важен!)
    dp.include_router(errors.router)
    dp.include_router(billing.router)
    dp.include_router(start.router)
    dp.include_router(translate.router)
    dp.include_router(inline.router)

    # Команды в меню бота
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start",  description="🚀 Главное меню"),
        BotCommand(command="tr",     description="🌍 Перевести сообщение (reply)"),
        BotCommand(command="to",     description="✏️ Перевести свой текст"),
        BotCommand(command="lang",   description="🔧 Изменить язык перевода"),
        BotCommand(command="quota",  description="📊 Баланс символов"),
        BotCommand(command="help",   description="❓ Помощь"),
    ])

    # Информация о боте
    bot_info = await bot.get_me()
    logger.info(
        "Bot ready",
        username=bot_info.username,
        id=bot_info.id,
    )

    # Запуск polling
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        # Graceful shutdown
        await bot.session.close()
        await close_redis()
        await close_session()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
