"""
Inline query handler.
@botname текст → показывает варианты перевода на топ-3 языка.
"""

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

logger = logging.getLogger(__name__)
router = Router(name="inline")

MIN_QUERY_LEN = 2
MAX_QUERY_LEN = 1000


@router.inline_query()
async def handle_inline_query(query: InlineQuery) -> None:
    text = query.query.strip()
    user = get_user(query.from_user.id)

    if len(text) < MIN_QUERY_LEN:
        await query.answer(
            results=[],
            switch_pm_text=t("inline_placeholder", user.ui_language),
            switch_pm_parameter="inline_help",
            cache_time=1,
        )
        return

    if len(text) > MAX_QUERY_LEN:
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

    # Берём топ-4 языка пользователя (без языка источника если определим)
    target_langs = user.favorite_langs[:4]

    # Переводим параллельно
    results = []
    tasks_done = 0

    for lang_code in target_langs:
        if tasks_done >= 4:
            break
        try:
            result = await translate(text, lang_code)

            flag = get_lang_flag(lang_code)
            lang_name = get_lang_name(lang_code)

            # Не показываем если перевод совпадает с оригиналом
            if result.translated_text.strip().lower() == text.lower():
                continue

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
            tasks_done += 1

        except Exception as e:
            logger.warning("Inline translate error for %s: %s", lang_code, e)
            continue

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
