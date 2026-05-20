"""
Обработчики команд перевода:
  /tr [lang]  — reply-перевод входящего сообщения
  /to [lang] [text] — перевод своего текста
"""

import html
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from services.translator import translate
from services.storage import get_user, deduct_chars
from keyboards.inline_kb import upgrade_kb, translate_result_kb, popular_langs_kb
from utils.languages import resolve_lang, get_lang_label, get_lang_name, get_lang_flag
from utils.i18n import t
from config import settings
from services.api_client import UserData

logger = logging.getLogger(__name__)
router = Router(name="translate")
MAX_RESULT_LENGTH = settings.max_result_length



# ── /tr ────────────────────────────────────────────────────

@router.message(Command("tr"))
async def cmd_tr(message: Message) -> None:
    """
    Переводит сообщение, на которое сделан reply.
    Использование:
      /tr            → переводит на язык пользователя по умолчанию
      /tr en         → переводит на английский
    """
    user = await get_user(message.from_user.id)

    if user.is_quota_exceeded:
        await _send_quota_exceeded(message, user)
        return

    # Разбираем аргументы
    args = message.text.split()[1:]
    target_lang = user.target_language

    if args:
        code = resolve_lang(args[0])
        if not code:
            await message.reply(
                t("tr_unknown_lang", user.ui_language, code=args[0]),
                parse_mode="HTML",
            )
            return
        target_lang = code

    # Получаем текст для перевода
    source_text: str | None = None
    source_msg = None

    if message.reply_to_message:
        source_msg = message.reply_to_message
        source_text = _extract_text(source_msg)
    else:
        await message.reply(
            t("tr_no_reply", user.ui_language),
            parse_mode="HTML",
        )
        return

    if not source_text:
        await message.reply(t("tr_no_text", user.ui_language))
        return

    # Проверяем лимит символов
    if len(source_text) > user.chars_remaining:
        await _send_quota_exceeded(message, user)
        return

    # Отправляем "печатает..."
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        result = await translate(source_text, target_lang)
    except ValueError as e:
        await message.reply(t("tr_error_value", user.ui_language, error=e))
        return
    except RuntimeError as e:
        logger.error("Translation error: %s", e)
        await message.reply(t("tr_error_runtime", user.ui_language))
        return

    # Списываем символы (только если не из кэша)
    if not result.cached:
        await deduct_chars(message.from_user.id, result.char_count)
        updated_user = await get_user(message.from_user.id)
    else:
        updated_user = user

    # Формируем ответ
    flag = get_lang_flag(result.target_lang)
    lang_name = get_lang_name(result.target_lang)

    # Краткая информация об источнике (имя отправителя) — экранируем HTML
    sender_name = html.escape(source_msg.from_user.first_name) if source_msg and source_msg.from_user else ""
    sender = t("tr_result_sender", user.ui_language, name=sender_name) if sender_name else ""

    cache_note = t("tr_result_cache", user.ui_language) if result.cached else ""

    header = t("tr_result_header", user.ui_language,
        flag=flag, lang=lang_name,
        sender=sender, cache_note=cache_note,
    )

    translated_text = result.translated_text
    # Разбиваем на части если длинный
    chunks = _split_message(translated_text, MAX_RESULT_LENGTH - len(header))

    # Сохраняем текст для retranslate
    _last_source_text[message.from_user.id] = source_text

    for i, chunk in enumerate(chunks):
        footer = ""
        if i == len(chunks) - 1:  # последний чанк — добавляем баланс
            footer = t("tr_result_footer", user.ui_language, chars=result.char_count, remaining=updated_user.chars_remaining)

        text = header + chunk + footer if i == 0 else chunk + footer

        await message.answer(
            text,
            reply_markup=translate_result_kb(
                result.source_lang, result.target_lang, source_text, user.ui_language
            ) if i == len(chunks) - 1 else None,
            parse_mode="HTML",
        )


# ── /to ────────────────────────────────────────────────────

@router.message(Command("to"))
async def cmd_to(message: Message) -> None:
    """
    Переводит произвольный текст.
    Использование:
      /to en Привет, как дела?
      /to de Что нового?
    """
    user = await get_user(message.from_user.id)

    if user.is_quota_exceeded:
        await _send_quota_exceeded(message, user)
        return

    # Парсим команду: /to [lang] [text...]
    parts = message.text.split(None, 2)  # ['/to', 'en', 'текст...']

    if len(parts) < 2:
        await message.reply(
            t("to_usage", user.ui_language),
            parse_mode="HTML",
        )
        return

    # Определяем язык
    code = resolve_lang(parts[1])
    if not code:
        await message.reply(
            t("to_usage", user.ui_language),
            parse_mode="HTML",
        )
        return

    target_lang = code
    text_to_translate = parts[2] if len(parts) > 2 else ""

    if not text_to_translate.strip():
        await message.reply(
            t("to_no_text", user.ui_language, lang=target_lang),
            parse_mode="HTML",
        )
        return

    if len(text_to_translate) > user.chars_remaining:
        await _send_quota_exceeded(message, user)
        return

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        result = await translate(text_to_translate, target_lang)
    except ValueError as e:
        await message.reply(t("tr_error_value", user.ui_language, error=e))
        return
    except RuntimeError:
        await message.reply(t("tr_error_runtime", user.ui_language))
        return

    if not result.cached:
        await deduct_chars(message.from_user.id, result.char_count)

    flag = get_lang_flag(result.target_lang)
    lang_name = get_lang_name(result.target_lang)
    cache_note = t("tr_result_cache", user.ui_language) if result.cached else ""

    text = t("to_result", user.ui_language,
        flag=flag, lang=lang_name, cache_note=cache_note, text=result.translated_text,
    )

    await message.reply(text, parse_mode="HTML")


# ── Retranslate (callback from /tr result) ──────────────────

@router.callback_query(F.data.startswith("retranslate:"))
async def cb_retranslate(callback: CallbackQuery) -> None:
    """Показывает список языков для повторного перевода."""
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        t("lang_popular", user.ui_language),
        reply_markup=popular_langs_kb(user.ui_language, callback_prefix="retranslate_to"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("retranslate_to:"))
async def cb_retranslate_to(callback: CallbackQuery) -> None:
    """Переводит сохранённый текст на выбранный язык."""
    user = await get_user(callback.from_user.id)
    target_lang = callback.data.split(":", 1)[1]

    original_text = _last_source_text.get(callback.from_user.id)
    if not original_text:
        await callback.answer(t("error_generic", user.ui_language), show_alert=True)
        return

    if user.is_quota_exceeded or len(original_text) > user.chars_remaining:
        await callback.message.edit_text(
            f"{t('quota_exceeded_title', user.ui_language)}\n\n"
            f"{t('quota_exceeded_used', user.ui_language, used=user.chars_used, limit=user.chars_limit)}\n\n"
            f"{t('quota_exceeded_options', user.ui_language)}",
            reply_markup=upgrade_kb(user.ui_language),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.bot.send_chat_action(callback.message.chat.id, "typing")
    await callback.answer()

    try:
        result = await translate(original_text, target_lang)
    except ValueError as e:
        await callback.message.edit_text(t("tr_error_value", user.ui_language, error=e))
        return
    except RuntimeError:
        await callback.message.edit_text(t("tr_error_runtime", user.ui_language))
        return

    if not result.cached:
        await deduct_chars(callback.from_user.id, result.char_count)
        updated_user = await get_user(callback.from_user.id)
    else:
        updated_user = user

    flag = get_lang_flag(result.target_lang)
    lang_name = get_lang_name(result.target_lang)

    header = t("tr_result_header", user.ui_language,
        flag=flag, lang=lang_name, sender="", cache_note="",
    )
    footer = t("tr_result_footer", user.ui_language, chars=result.char_count, remaining=updated_user.chars_remaining)

    text = header + result.translated_text + footer

    await callback.message.edit_text(
        text,
        reply_markup=translate_result_kb(
            result.source_lang, result.target_lang, original_text, user.ui_language
        ),
        parse_mode="HTML",
    )


# ── Helpers ─────────────────────────────────────────────────

def _extract_text(msg: Message) -> str | None:
    """Извлекает текст из сообщения (text / caption)."""
    return msg.text or msg.caption or None


def _split_message(text: str, max_len: int) -> list[str]:
    """Разбивает текст на части, не разрезая слова."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    return chunks


async def _send_quota_exceeded(message: Message, user: UserData) -> None:
    """Сообщение о превышении квоты."""
    text = (
        f"{t('quota_exceeded_title', user.ui_language)}\n\n"
        f"{t('quota_exceeded_used', user.ui_language, used=user.chars_used, limit=user.chars_limit)}\n\n"
        f"{t('quota_exceeded_options', user.ui_language)}"
    )
    await message.reply(text, reply_markup=upgrade_kb(user.ui_language), parse_mode="HTML")
