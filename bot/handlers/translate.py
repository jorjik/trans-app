"""
Обработчики команд перевода:
  /tr [lang]  — reply-перевод входящего сообщения
  /to [lang] [text] — перевод своего текста
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.translator import translate
from services.storage import get_user, deduct_chars
from keyboards.inline_kb import upgrade_kb, translate_result_kb
from utils.languages import resolve_lang, get_lang_label, get_lang_name, get_lang_flag

logger = logging.getLogger(__name__)
router = Router(name="translate")

MAX_RESULT_LENGTH = 4096  # Telegram message limit


# ── /tr ────────────────────────────────────────────────────

@router.message(Command("tr"))
async def cmd_tr(message: Message) -> None:
    """
    Переводит сообщение, на которое сделан reply.
    Использование:
      /tr            → переводит на язык пользователя по умолчанию
      /tr en         → переводит на английский
    """
    user = get_user(message.from_user.id)

    # Проверка квоты
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
                f"❌ Не знаю язык <code>{args[0]}</code>.\n"
                f"Примеры: /tr en · /tr de · /tr fr · /tr uk",
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
            "ℹ️ Сделай <b>reply</b> на сообщение которое хочешь перевести, "
            "затем напиши /tr\n\n"
            "Или используй: /to en Привет как дела",
            parse_mode="HTML",
        )
        return

    if not source_text:
        await message.reply("❌ В том сообщении нет текста для перевода.")
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
        await message.reply(f"❌ Ошибка: {e}")
        return
    except RuntimeError as e:
        logger.error("Translation error: %s", e)
        await message.reply("❌ Не удалось перевести. Попробуй ещё раз.")
        return

    # Списываем символы (только если не из кэша)
    if not result.cached:
        deduct_chars(message.from_user.id, result.char_count)
        updated_user = get_user(message.from_user.id)
    else:
        updated_user = user

    # Формируем ответ
    flag = get_lang_flag(result.target_lang)
    lang_name = get_lang_name(result.target_lang)

    # Краткая информация об источнике (имя отправителя)
    sender = ""
    if source_msg and source_msg.from_user:
        sender = f" · от {source_msg.from_user.first_name}"

    cache_note = " · 📦 кэш" if result.cached else ""

    header = (
        f"{flag} <b>{lang_name}</b>"
        f"{sender}"
        f"{cache_note}\n"
        f"━━━━━━━━━━━━━━\n"
    )

    translated_text = result.translated_text
    # Разбиваем на части если длинный
    chunks = _split_message(translated_text, MAX_RESULT_LENGTH - len(header))

    for i, chunk in enumerate(chunks):
        footer = ""
        if i == len(chunks) - 1:  # последний чанк — добавляем баланс
            footer = (
                f"\n━━━━━━━━━━━━━━\n"
                f"💬 {result.char_count} симв. · "
                f"осталось {updated_user.chars_remaining:,}"
            )

        text = header + chunk + footer if i == 0 else chunk + footer

        await message.answer(
            text,
            reply_markup=translate_result_kb(
                result.source_lang, result.target_lang, source_text
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
    user = get_user(message.from_user.id)

    if user.is_quota_exceeded:
        await _send_quota_exceeded(message, user)
        return

    # Парсим команду: /to [lang] [text...]
    parts = message.text.split(None, 2)  # ['/to', 'en', 'текст...']

    if len(parts) < 2:
        await message.reply(
            "ℹ️ Использование:\n"
            "<code>/to en Текст для перевода</code>\n\n"
            "Примеры:\n"
            "/to en Привет, как дела?\n"
            "/to de Что нового?\n"
            "/to fr Спасибо большое",
            parse_mode="HTML",
        )
        return

    # Определяем язык
    code = resolve_lang(parts[1])
    if not code:
        # Может быть пользователь не указал язык, а сразу написал текст
        # Тогда используем язык по умолчанию
        target_lang = user.target_language
        text_to_translate = message.text.split(None, 1)[1] if len(parts) > 1 else ""
    else:
        target_lang = code
        text_to_translate = parts[2] if len(parts) > 2 else ""

    if not text_to_translate.strip():
        await message.reply(
            f"ℹ️ Укажи текст для перевода:\n"
            f"<code>/to {target_lang} Твой текст здесь</code>",
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
        await message.reply(f"❌ {e}")
        return
    except RuntimeError:
        await message.reply("❌ Не удалось перевести. Попробуй ещё раз.")
        return

    if not result.cached:
        deduct_chars(message.from_user.id, result.char_count)

    flag = get_lang_flag(result.target_lang)
    lang_name = get_lang_name(result.target_lang)
    cache_note = " · 📦" if result.cached else ""

    text = (
        f"{flag} <b>{lang_name}</b>{cache_note}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{result.translated_text}"
    )

    await message.reply(text, parse_mode="HTML")


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


async def _send_quota_exceeded(message: Message, user) -> None:
    """Сообщение о превышении квоты."""
    text = (
        "🚫 <b>Лимит символов исчерпан</b>\n\n"
        f"Использовано: {user.chars_used:,} / {user.chars_limit:,}\n\n"
        "Что можно сделать:\n"
        "• ⭐ Апгрейд до Starter — 500k символов за 250 Stars/мес\n"
        "• 👥 Пригласи друга — получи +10,000 символов бесплатно\n"
        "• 📅 Подожди сброса лимита (1-е число месяца)"
    )
    await message.reply(text, reply_markup=upgrade_kb(), parse_mode="HTML")
