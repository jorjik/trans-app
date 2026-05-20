"""
Inline query handler.
@botname текст → показывает варианты перевода на топ-3 языка.
"""

import asyncio
import logging
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from services.translator import translate
from services.storage import get_user
from utils.languages import get_lang_flag, get_lang_name
from utils.i18n import t
from config import settings

logger = logging.getLogger(__name__)
router = Router(name="inline")


@router.inline_query()
async def handle_inline_query(query: InlineQuery) -> None:
    text = query.query.strip()
    user = await get_user(query.from_user.id)

    if len(text) < settings.min_inline_query_len:
        await query.answer(
            results=[],
            switch_pm_text=t("inline_placeholder", user.ui_language),
            switch_pm_parameter="inline_help",
            cache_time=1,
        )
        return

    if len(text) > settings.max_inline_query_len:
        await query.answer(
            results=[],
            switch_pm_text=t("inline_too_long", user.ui_language),
            switch_pm_parameter="inline_help",
            cache_time=1,
        )
        return

    if user.is_quota_exceeded:
        await query.answer(
            results=[],
            switch_pm_text=t("inline_quota_exceeded", user.ui_language),
            switch_pm_parameter="upgrade",
            cache_time=5,
        )
        return

    # Берём топ-4 языка пользователя
    target_langs = user.favorite_langs[:4]

    # Параллельный перевод через asyncio.gather
    sem = asyncio.Semaphore(3)  # ограничиваем конкурентность

    async def _translate_one(lang: str):
        async with sem:
            return lang, await translate(text, lang)

    tasks = [_translate_one(lang) for lang in target_langs]
    completed = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for item in completed:
        if isinstance(item, Exception):
            continue
        lang_code, result = item

        # Не показываем если перевод совпадает с оригиналом
        if result.translated_text.strip().lower() == text.lower():
            continue

        flag = get_lang_flag(lang_code)
        lang_name = get_lang_name(lang_code)

        article = InlineQueryResultArticle(
            id=f"translate_{lang_code}",
            title=f"{flag} {lang_name}",
            description=result.translated_text[:100],
            input_message_content=InputTextMessageContent(
                message_text=result.translated_text,
            ),
            thumb_url=None,
        )
        results.append(article)

    if not results:
        await query.answer(
            results=[],
            switch_pm_text=t("inline_error", user.ui_language),
            switch_pm_parameter="help",
            cache_time=1,
        )
        return

    await query.answer(
        results=results,
        cache_time=30,
        is_personal=True,
    )
