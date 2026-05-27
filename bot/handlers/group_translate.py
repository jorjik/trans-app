"""
Обработчик /group_translate — автоперевод сообщений в мультиязычных группах.

Команды (только для админов группы):
  /group_translate        — показать текущий статус
  /group_translate on     — включить автоперевод
  /group_translate off    — выключить автоперевод
  /group_translate target [lang] — задать язык перевода

Когда перевод включён, каждое текстовое сообщение в группе переводится
на целевой язык и отправляется как ответ (reply).

Важно: бот должен быть добавлен в группу как администратор с правом
чтения всех сообщений (Privacy Mode выключен в BotFather).
"""

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import Message, ChatMemberUpdated

from services.storage import get_user, deduct_chars, get_group_config, update_group_config
from services.translator import translate as do_translate
from utils.languages import resolve_lang, get_lang_flag, get_lang_name
from utils.i18n import t

logger = logging.getLogger(__name__)
router = Router(name="group_translate")

# Локальный кэш активных групп: chat_id -> config dict
_active_groups: dict[int, dict] = {}


async def _refresh_group_cache(chat_id: int) -> dict | None:
    """Обновляет кэш для одного чата из API. Возвращает config dict или None."""
    try:
        data = await get_group_config(chat_id)
        if data and data.get("exists") and data.get("is_active"):
            _active_groups[chat_id] = data
            return data
        else:
            _active_groups.pop(chat_id, None)
            return None
    except Exception:
        _active_groups.pop(chat_id, None)
        return None


# ── /group_translate command ─────────────────────────────────

@router.message(Command("group_translate"))
async def cmd_group_translate(message: Message) -> None:
    """Обрабатывает /group_translate [on|off|target [lang]]."""

    # Проверяем, что команда вызвана в группе
    if message.chat.type not in ("group", "supergroup"):
        # Fallback: пытаемся получить язык пользователя для ответа
        user = await get_user(message.from_user.id)
        ui_lang = user.ui_language or "en" if user else "en"
        await message.reply(t("group_translate_group_only", ui_lang))
        return

    # Язык интерфейса — берём у пользователя, вызвавшего команду
    user = await get_user(message.from_user.id)
    ui_lang = user.ui_language or "en"

    # Проверяем, что пользователь — админ группы
    chat_member = await message.bot.get_chat_member(
        message.chat.id, message.from_user.id
    )
    if chat_member.status not in ("creator", "administrator"):
        await message.reply(t("group_translate_only_admin", ui_lang))
        return

    args = message.text.split()[1:]  # всё после /group_translate
    chat_id = message.chat.id
    chat_title = message.chat.title or f"Chat {chat_id}"

    if not args:
        # Показываем статус
        config = await get_group_config(chat_id)
        if config and config.get("exists") and config.get("is_active"):
            code = config.get("target_lang", "en")
            flag = get_lang_flag(code)
            name = get_lang_name(code)
            await message.reply(
                t("group_translate_status_on", ui_lang, flag=flag, name=name, code=code)
            )
        else:
            await message.reply(t("group_translate_status_off", ui_lang))
        return

    cmd = args[0].lower()

    if cmd == "on":
        target_lang = "en"
        if len(args) > 1:
            code = resolve_lang(args[1])
            if code:
                target_lang = code
            else:
                await message.reply(t("lang_unknown", ui_lang, code=args[1]))
                return

        await update_group_config(
            chat_id=chat_id,
            chat_title=chat_title,
            target_lang=target_lang,
            is_active=True,
            translator_uid=message.from_user.id,
        )
        # Обновляем кэш
        await _refresh_group_cache(chat_id)
        flag = get_lang_flag(target_lang)
        name = get_lang_name(target_lang)
        await message.reply(
            t("group_translate_enabled", ui_lang, flag=flag, name=name)
        )

    elif cmd == "off":
        await update_group_config(
            chat_id=chat_id,
            chat_title=chat_title,
            is_active=False,
        )
        _active_groups.pop(chat_id, None)
        await message.reply(t("group_translate_disabled", ui_lang))

    elif cmd == "target":
        if len(args) < 2:
            await message.reply(t("group_translate_target_hint", ui_lang))
            return
        code = resolve_lang(args[1])
        if not code:
            await message.reply(t("lang_unknown", ui_lang, code=args[1]))
            return
        flag = get_lang_flag(code)
        name = get_lang_name(code)

        data = await get_group_config(chat_id)
        is_active = data.get("is_active", False) if data else False
        await update_group_config(
            chat_id=chat_id,
            chat_title=chat_title,
            target_lang=code,
            is_active=is_active,
        )
        if is_active:
            await _refresh_group_cache(chat_id)

        await message.reply(
            t("group_translate_target_set", ui_lang, flag=flag, name=name, code=code)
        )

    else:
        await message.reply(t("group_translate_usage", ui_lang))


# ── Group message interceptor ────────────────────────────────

@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.is_not(None),
    ~F.text.startswith("/"),
)
async def on_group_message(message: Message) -> None:
    """Переводит сообщения в группах с включённым автопереводом."""

    chat_id = message.chat.id

    # Пытаемся получить конфиг из кэша; если нет — проверяем API (1 вызов)
    config = _active_groups.get(chat_id)
    if config is None:
        config = await _refresh_group_cache(chat_id)
        if config is None:
            return  # группа не активна

    # Пропускаем сообщения от ботов
    if not message.text or (message.from_user and message.from_user.is_bot):
        return

    text = message.text.strip()
    if len(text) < 2:
        return

    target_lang = config.get("target_lang", "en")
    translator_uid = config.get("translator_uid")

    if not translator_uid:
        return

    # Квоту списываем с админа, включившего перевод
    admin_user = await get_user(translator_uid)
    if admin_user.is_quota_exceeded or len(text) > admin_user.chars_remaining:
        logger.warning("Group %s: admin %s quota exceeded", chat_id, translator_uid)
        return

    await message.bot.send_chat_action(chat_id, "typing")

    try:
        result = await do_translate(text, target_lang)
    except (ValueError, RuntimeError) as e:
        logger.error("Group translate error in %s: %s", chat_id, e)
        return

    if not result.cached:
        await deduct_chars(translator_uid, result.char_count)

    # Формируем ответ с переводом
    source_flag = get_lang_flag(result.source_lang)
    source_name = get_lang_name(result.source_lang)
    target_flag = get_lang_flag(result.target_lang)
    target_name = get_lang_name(result.target_lang)
    sender_name = html.escape(message.from_user.first_name) if message.from_user else ""

    translation_text = (
        f"{source_flag} <b>{source_name}</b> → {target_flag} <b>{target_name}</b>\n"
        f"┌─ <i>от {sender_name}</i>\n"
        f"└─ {result.translated_text}"
    )

    max_len = 4000
    if len(translation_text) > max_len:
        translation_text = translation_text[:max_len - 3] + "..."

    await message.reply(translation_text, parse_mode="HTML")


# ── Bot added to / removed from group ────────────────────────

@router.my_chat_member(ChatMemberUpdatedFilter(
    member_status_changed=IS_NOT_MEMBER >> IS_MEMBER
))
async def on_bot_added(event: ChatMemberUpdated) -> None:
    """Когда бота добавили в группу — приветствие."""
    chat = event.chat
    if chat.type not in ("group", "supergroup"):
        return
    # Определяем язык чата по языку админа, добавившего бота
    # (from_user — это тот, кто добавил бота)
    ui_lang = "en"
    if event.from_user:
        try:
            user = await get_user(event.from_user.id)
            ui_lang = user.ui_language or "en"
        except Exception:
            pass

    await event.bot.send_message(
        chat.id,
        t("group_translate_bot_welcome", ui_lang),
        parse_mode="HTML",
    )


@router.my_chat_member(ChatMemberUpdatedFilter(
    member_status_changed=IS_MEMBER >> IS_NOT_MEMBER
))
async def on_bot_removed(event: ChatMemberUpdated) -> None:
    """Когда бота удалили из группы — чистим кэш."""
    _active_groups.pop(event.chat.id, None)
    logger.info("Bot removed from chat %s, cleaned up", event.chat.id)
