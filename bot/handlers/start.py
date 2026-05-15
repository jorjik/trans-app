"""Обработчик /start и главного меню."""

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode

from services.storage import get_user, set_target_language
from keyboards.inline_kb import main_menu_kb, change_lang_kb, popular_langs_kb, upgrade_kb
from utils.languages import get_lang_label, resolve_lang, get_lang_name
from config import settings

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = get_user(message.from_user.id)
    name = message.from_user.first_name or "друг"

    text = (
        f"Привет, {hbold(name)}! 👋\n\n"
        f"Я — твой личный переводчик поверх Telegram.\n\n"
        f"<b>Что я умею:</b>\n"
        f"• <b>/tr</b> (reply) — перевести сообщение только для тебя\n"
        f"• <b>/to [язык] текст</b> — перевести свой текст\n"
        f"• <b>@{(await message.bot.get_me()).username} текст</b> — inline-перевод в любом чате\n\n"
        f"🌍 Текущий язык: {get_lang_label(user.target_language)}\n"
        f"📊 Баланс: {user.chars_remaining:,} / {user.chars_limit:,} символов\n"
    )

    await message.answer(
        text,
        reply_markup=main_menu_kb(settings.mini_app_url),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>📖 Как пользоваться TransApp</b>\n\n"
        "<b>Перевод входящих сообщений:</b>\n"
        "1. Сделай reply на любое сообщение\n"
        "2. Напиши /tr — я переведу только для тебя\n"
        "3. Или /tr en — перевести на конкретный язык\n\n"
        "<b>Перевод своего текста:</b>\n"
        "/to en Привет, как дела?\n"
        "→ Hello, how are you?\n\n"
        "<b>Inline-режим (в любом чате):</b>\n"
        "Напиши @botusername и текст — выбери язык из списка\n\n"
        "<b>Настройки:</b>\n"
        "/lang — изменить язык по умолчанию\n"
        "/quota — посмотреть баланс символов\n\n"
        "<b>Коды языков:</b>\n"
        "en, ru, de, fr, es, it, pl, uk, tr, ar, zh, ja, ko...\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("lang"))
async def cmd_lang(message: Message) -> None:
    user = get_user(message.from_user.id)

    # /lang de — сразу устанавливаем язык
    args = message.text.split()[1:]
    if args:
        code = resolve_lang(args[0])
        if not code:
            await message.answer(
                f"❌ Не знаю язык <code>{args[0]}</code>.\n"
                "Попробуй: en, ru, de, fr, es, uk, pl...",
                parse_mode="HTML",
            )
            return
        updated = set_target_language(message.from_user.id, code)
        await message.answer(
            f"✅ Язык по умолчанию: {get_lang_label(code)}\n"
            f"Все переводы теперь будут на {get_lang_name(code)}.",
            parse_mode="HTML",
        )
        return

    # Показываем клавиатуру выбора
    await message.answer(
        f"🌍 Текущий язык: {get_lang_label(user.target_language)}\n\n"
        "Выбери язык для перевода:",
        reply_markup=change_lang_kb(user.favorite_langs),
        parse_mode="HTML",
    )


@router.message(Command("quota"))
async def cmd_quota(message: Message) -> None:
    user = get_user(message.from_user.id)

    # Процент использования
    pct = (user.chars_used / user.chars_limit * 100) if user.chars_limit > 0 else 0
    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    plan_emoji = {"free": "🆓", "starter": "⭐", "pro": "💎", "business": "🏢"}

    text = (
        f"<b>📊 Твой баланс</b>\n\n"
        f"Тариф: {plan_emoji.get(user.plan, '❓')} {user.plan.capitalize()}\n\n"
        f"Символов использовано:\n"
        f"[{bar}] {pct:.1f}%\n"
        f"{user.chars_used:,} / {user.chars_limit:,}\n\n"
        f"Осталось: <b>{user.chars_remaining:,}</b> символов\n"
    )

    if user.plan == "free":
        text += "\n💡 <i>Апгрейд до Starter: 500k символов за 250 ⭐/мес</i>"

    kb = None
    if user.chars_remaining < user.chars_limit * 0.2:
        kb = upgrade_kb()

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ── Callbacks ──────────────────────────────────────────────

@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await cmd_help(callback.message)


@router.callback_query(F.data == "quota")
async def cb_quota(callback: CallbackQuery) -> None:
    await callback.answer()
    await cmd_quota(callback.message)


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"🌍 Текущий язык: {get_lang_label(user.target_language)}\n\nВыбери язык:",
        reply_markup=change_lang_kb(user.favorite_langs),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "search_lang")
async def cb_search_lang(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🌍 Выбери один из популярных языков:",
        reply_markup=popular_langs_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_lang(callback: CallbackQuery) -> None:
    code = callback.data.split(":")[1]
    updated = set_target_language(callback.from_user.id, code)
    await callback.answer(f"✅ Язык: {get_lang_label(code)}", show_alert=False)
    await callback.message.edit_text(
        f"✅ Язык перевода изменён на {get_lang_label(code)}\n\n"
        f"Теперь /tr будет переводить на <b>{get_lang_name(code)}</b>.",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "dismiss")
async def cb_dismiss(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery) -> None:
    await callback.answer()
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"🌍 Текущий язык: {get_lang_label(user.target_language)}\n"
        f"📊 Баланс: {user.chars_remaining:,} символов",
        reply_markup=main_menu_kb(settings.mini_app_url),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery) -> None:
    bot = callback.bot
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.answer()
    await callback.message.answer(
        f"👥 <b>Пригласи друга — получи +10,000 символов!</b>\n\n"
        f"Твоя реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"Когда друг сделает первый перевод — вы оба получите бонус.",
        parse_mode="HTML",
    )
