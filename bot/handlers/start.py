"""Обработчик /start и главного меню."""

import logging

import aiohttp
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold

from services.storage import get_user, set_target_language, sync_ui_language
from keyboards.inline_kb import main_menu_reply_kb, change_lang_kb, popular_langs_kb, upgrade_kb, back_main_kb, ui_lang_kb
from utils.languages import get_lang_label, resolve_lang, get_lang_name, get_lang_flag, UI_LANGUAGES
from utils.i18n import t, PLAN_EMOJI, plan_name
from config import settings

logger = logging.getLogger(__name__)
router = Router(name="start")


async def _sync_ui_lang(telegram_id: int, ui_language: str) -> None:
    """Синхронизирует ui_language с API (ботовый internal endpoint)."""
    if not settings.api_url:
        return
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{settings.api_url}/internal/sync-ui-lang",
                json={"telegram_id": telegram_id, "ui_language": ui_language},
                headers={"X-Bot-Secret": settings.bot_internal_secret},
                timeout=aiohttp.ClientTimeout(total=5),
            )
    except Exception as e:
        logger.warning("sync-ui-lang failed for %s: %s", telegram_id, e)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    if command.args:
        args = command.args.strip()
        if args.startswith("pay_"):
            from services.billing import start_checkout

            plan_id = args.removeprefix("pay_").split("_", 1)[0]
            await start_checkout(message, plan_id)
            return

    user = await get_user(message.from_user.id)

    # Всегда показываем выбор языка интерфейса при /start
    tg_lang = (message.from_user.language_code or "en")[:2]
    if tg_lang not in UI_LANGUAGES:
        tg_lang = "en"

    await message.answer(
        "🌐 <b>Welcome! / Ласкаво просимо! / Добро пожаловать!</b>\n\n"
        "Choose your interface language:\n"
        "Оберіть мову інтерфейсу:\n"
        "Выберите язык интерфейса:",
        reply_markup=ui_lang_kb(tg_lang),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user = await get_user(message.from_user.id)
    text = (
        f"<b>{t('help_title', user.ui_language)}</b>\n\n"
        f"<b>{t('help_incoming_title', user.ui_language)}</b>\n"
        f"{t('help_incoming_1', user.ui_language)}\n"
        f"{t('help_incoming_2', user.ui_language)}\n"
        f"{t('help_incoming_3', user.ui_language)}\n\n"
        f"<b>{t('help_own_title', user.ui_language)}</b>\n"
        f"{t('help_own_example', user.ui_language)}\n"
        f"{t('help_own_result', user.ui_language)}\n\n"
        f"<b>{t('help_inline_title', user.ui_language)}</b>\n"
        f"{t('help_inline_text', user.ui_language)}\n\n"
        f"<b>{t('help_settings_title', user.ui_language)}</b>\n"
        f"{t('help_settings_lang', user.ui_language)}\n"
        f"{t('help_settings_quota', user.ui_language)}\n\n"
        f"<b>{t('help_autotranslate_title', user.ui_language)}</b>\n"
        f"{t('help_autotranslate_text', user.ui_language)}\n\n"
        f"<b>{t('help_group_title', user.ui_language)}</b>\n"
        f"{t('help_group_text', user.ui_language)}\n\n"
        f"<b>{t('help_codes_title', user.ui_language)}</b>\n"
        f"{t('help_codes', user.ui_language)}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("lang"))
async def cmd_lang(message: Message) -> None:
    user = await get_user(message.from_user.id)

    # /lang de — сразу устанавливаем язык
    args = message.text.split()[1:]
    if args:
        code = resolve_lang(args[0])
        if not code:
            await message.answer(
                t("lang_unknown", user.ui_language, code=args[0]),
                parse_mode="HTML",
            )
            return
        await set_target_language(message.from_user.id, code)
        await message.answer(
            t("lang_set", user.ui_language, label=get_lang_label(code), name=get_lang_name(code)),
            parse_mode="HTML",
        )
        return

    # Показываем клавиатуру выбора
    await message.answer(
        t("lang_current", user.ui_language, label=get_lang_label(user.target_language)),
        reply_markup=change_lang_kb(user.favorite_langs, user.ui_language),
        parse_mode="HTML",
    )


@router.message(Command("quota"))
async def cmd_quota(message: Message) -> None:
    user = await get_user(message.from_user.id)

    # Процент использования
    pct = (user.chars_used / user.chars_limit * 100) if user.chars_limit > 0 else 0
    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    text = (
        f"<b>{t('quota_title', user.ui_language)}</b>\n\n"
        f"{t('quota_plan', user.ui_language, emoji=PLAN_EMOJI.get(user.plan, '❓'), plan=plan_name(user.plan, user.ui_language))}\n\n"
        f"{t('quota_used', user.ui_language)}\n"
        f"[{bar}] {pct:.1f}%\n"
        f"{t('quota_used_limit', user.ui_language, used=user.chars_used, limit=user.chars_limit)}\n\n"
        f"{t('quota_remaining', user.ui_language, remaining=user.chars_remaining)}\n"
    )

    if user.plan == "free":
        text += "\n" + t("quota_upgrade_hint", user.ui_language)

    # Всегда показываем клавиатуру с кнопкой "Назад"
    kb = upgrade_kb(user.ui_language) if user.chars_remaining < user.chars_limit * 0.2 or user.plan == "free" else back_main_kb(user.ui_language)

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("appss_verify"))
async def cmd_appss_verify(message: Message) -> None:
    """Команда для верификации."""
    await message.answer("appss_17fbd8")


@router.message(Command("uilang"))
async def cmd_uilang(message: Message) -> None:
    """Команда для смены языка интерфейса бота и Mini App."""
    user = await get_user(message.from_user.id)

    # /uilang ru — сразу устанавливаем
    args = message.text.split()[1:]
    if args:
        code = args[0].strip().lower()
        if code in UI_LANGUAGES:
            await sync_ui_language(message.from_user.id, code)
            await _sync_ui_lang(message.from_user.id, code)
            user2 = await get_user(message.from_user.id)
            await message.answer(
                t("uilang_set", user2.ui_language, label=get_lang_label(code)),
                parse_mode="HTML",
            )
            return
        else:
            await message.answer(
                "❌ " + t("lang_unknown", user.ui_language, code=args[0]),
                parse_mode="HTML",
            )
            return

    await message.answer(
        t("uilang_current", user.ui_language, label=get_lang_label(user.ui_language)),
        reply_markup=ui_lang_kb(user.ui_language),
        parse_mode="HTML",
    )


# ── Callbacks ──────────────────────────────────────────────

@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    text = (
        f"<b>{t('help_title', user.ui_language)}</b>\n\n"
        f"<b>{t('help_incoming_title', user.ui_language)}</b>\n"
        f"{t('help_incoming_1', user.ui_language)}\n"
        f"{t('help_incoming_2', user.ui_language)}\n"
        f"{t('help_incoming_3', user.ui_language)}\n\n"
        f"<b>{t('help_own_title', user.ui_language)}</b>\n"
        f"{t('help_own_example', user.ui_language)}\n"
        f"{t('help_own_result', user.ui_language)}\n\n"
        f"<b>{t('help_inline_title', user.ui_language)}</b>\n"
        f"{t('help_inline_text', user.ui_language)}\n\n"
        f"<b>{t('help_settings_title', user.ui_language)}</b>\n"
        f"{t('help_settings_lang', user.ui_language)}\n"
        f"{t('help_settings_quota', user.ui_language)}\n\n"
        f"<b>{t('help_codes_title', user.ui_language)}</b>\n"
        f"{t('help_codes', user.ui_language)}"
    )
    await callback.message.edit_text(text, reply_markup=back_main_kb(user.ui_language), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "quota")
async def cb_quota(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    pct = (user.chars_used / user.chars_limit * 100) if user.chars_limit > 0 else 0
    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    text = (
        f"<b>{t('quota_title', user.ui_language)}</b>\n\n"
        f"{t('quota_plan', user.ui_language, emoji=PLAN_EMOJI.get(user.plan, '❓'), plan=plan_name(user.plan, user.ui_language))}\n\n"
        f"{t('quota_used', user.ui_language)}\n"
        f"[{bar}] {pct:.1f}%\n"
        f"{t('quota_used_limit', user.ui_language, used=user.chars_used, limit=user.chars_limit)}\n\n"
        f"{t('quota_remaining', user.ui_language, remaining=user.chars_remaining)}\n"
    )
    if user.plan == "free":
        text += "\n" + t("quota_upgrade_hint", user.ui_language)

    kb = upgrade_kb(user.ui_language) if user.chars_remaining < user.chars_limit * 0.2 or user.plan == "free" else back_main_kb(user.ui_language)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        t("lang_choose", user.ui_language, label=get_lang_label(user.target_language)),
        reply_markup=change_lang_kb(user.favorite_langs, user.ui_language),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "search_lang")
async def cb_search_lang(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        t("lang_popular", user.ui_language),
        reply_markup=popular_langs_kb(user.ui_language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_lang(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    code = callback.data.split(":")[1]
    await set_target_language(callback.from_user.id, code)
    await callback.answer(t("lang_set_success", user.ui_language, label=get_lang_label(code)), show_alert=False)
    await callback.message.edit_text(
        t("lang_set_done", user.ui_language, label=get_lang_label(code), name=get_lang_name(code)),
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
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        t("back_main_status", user.ui_language, label=get_lang_label(user.target_language), remaining=user.chars_remaining),
        parse_mode="HTML",
    )
    # Reply-клавиатура уже установлена и видна внизу — кнопки не дублируем


# ── Reply keyboard handlers ──────────────────────────────────

@router.message(F.text.in_([
    t("btn_how_to_use", lang)
    for lang in UI_LANGUAGES
]))
async def on_how_to_use_button(message: Message) -> None:
    await cmd_help(message)


@router.message(F.text.in_([
    t("btn_change_lang", lang)
    for lang in UI_LANGUAGES
]))
async def on_change_lang_button(message: Message) -> None:
    user = await get_user(message.from_user.id)
    await message.answer(
        t("lang_current", user.ui_language, label=get_lang_label(user.target_language)),
        reply_markup=change_lang_kb(user.favorite_langs, user.ui_language),
        parse_mode="HTML",
    )


@router.message(F.text.in_([
    t("btn_my_balance", lang)
    for lang in UI_LANGUAGES
]))
async def on_my_balance_button(message: Message) -> None:
    await cmd_quota(message)


# ── Admin reply button ─────────────────────────────────────

@router.message(F.text == "⚙️ Admin")
async def on_admin_button(message: Message) -> None:
    from handlers.admin import cmd_admin
    await cmd_admin(message)


@router.callback_query(F.data.startswith("set_ui_lang:"))
async def cb_set_ui_lang(callback: CallbackQuery) -> None:
    code = callback.data.split(":")[1]
    logger.info("cb_set_ui_lang: user=%s code=%s api_url=%s", callback.from_user.id, code, settings.api_url)
    try:
        await sync_ui_language(callback.from_user.id, code)
        logger.info("cb_set_ui_lang: sync_ui_language OK")
    except Exception as e:
        logger.error("cb_set_ui_lang: sync_ui_language failed: %s", e, exc_info=True)
    try:
        await _sync_ui_lang(callback.from_user.id, code)
        logger.info("cb_set_ui_lang: _sync_ui_lang OK")
    except Exception as e:
        logger.error("cb_set_ui_lang: _sync_ui_lang failed: %s", e, exc_info=True)
    try:
        user = await get_user(callback.from_user.id)
        logger.info("cb_set_ui_lang: get_user OK ui_lang=%s", user.ui_language)
    except Exception as e:
        logger.error("cb_set_ui_lang: get_user failed: %s", e, exc_info=True)
        user = None

    # Всегда отвечаем на callback, чтобы Telegram убрал loading
    await callback.answer("✅ " + get_lang_label(code))

    if user:
        try:
            name = callback.from_user.first_name or t("start_friend", user.ui_language)
            bot_me = await callback.bot.get_me()

            text = t("start_greeting", user.ui_language,
                name=hbold(name),
                bot_username=bot_me.username,
                target_lang=get_lang_label(user.target_language),
                chars_remaining=user.chars_remaining,
                chars_limit=user.chars_limit,
            )
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
            )

            # Показываем reply-клавиатуру внизу (один раз, после выбора языка)
            try:
                await callback.message.answer(
                    "💡 " + t("reply_menu_hint", user.ui_language),
                    reply_markup=main_menu_reply_kb(user.ui_language, user_id=callback.from_user.id),
                )
            except Exception as e2:
                logger.error("cb_set_ui_lang: reply kb failed: %s", e2, exc_info=True)
        except Exception as e:
            logger.error("cb_set_ui_lang: show main menu failed: %s", e, exc_info=True)


@router.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery) -> None:
    user = await get_user(callback.from_user.id)
    bot = callback.bot
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.answer()
    await callback.message.answer(
        f"{t('referral_title', user.ui_language)}\n\n"
        f"{t('referral_text', user.ui_language, link=ref_link)}",
        parse_mode="HTML",
    )
