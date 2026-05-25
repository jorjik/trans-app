"""Админ-панель — /admin, статистика, управление ботом."""

import logging

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import settings
from services.storage import get_user
from utils.i18n import t
from keyboards.inline_kb import admin_menu_kb, admin_payment_kb, back_main_kb

logger = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_tg_ids


async def _fetch_admin_stats() -> dict | None:
    """Запрашивает статистику из API /admin/stats."""
    if not settings.api_url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.api_url}/admin/stats",
                headers={"X-Bot-Secret": settings.bot_internal_secret},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("admin/stats returned %s", resp.status)
                return None
    except Exception as e:
        logger.warning("admin/stats failed: %s", e)
        return None


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Команда /admin — админ-панель."""
    if not _is_admin(message.from_user.id):
        await message.answer(t("admin_access_denied", "en"))
        return

    user = await get_user(message.from_user.id)
    await message.answer(
        f"⚙️ <b>{t('admin_panel', user.ui_language)}</b>\n\n"
        f"{t('admin_choose_option', user.ui_language)}:",
        reply_markup=admin_menu_kb(user.ui_language),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    """Показывает общую статистику бота."""
    if not _is_admin(callback.from_user.id):
        await callback.answer(t("admin_access_denied", "en"))
        return

    await callback.answer(t("admin_loading", "en"))
    user = await get_user(callback.from_user.id)
    lang = user.ui_language

    stats = await _fetch_admin_stats()
    if not stats:
        await callback.message.edit_text(
            t("admin_no_stats", lang),
            reply_markup=admin_menu_kb(lang),
        )
        return

    def fmt(n: int) -> str:
        return f"{n:,}"

    # Users by plan
    plans_text = ""
    plans_order = ["free", "starter", "pro", "business"]
    plan_emojis = {"free": "🆓", "starter": "⭐", "pro": "💎", "business": "🏢"}
    for plan in plans_order:
        count = stats.get("users_by_plan", {}).get(plan, 0)
        if count:
            emoji = plan_emojis.get(plan, "❓")
            plans_text += f"  {emoji} {plan.capitalize()}: {fmt(count)}\n"

    # Top languages
    top_langs_text = ""
    for lang_data in stats.get("top_languages", []):
        lang_code = lang_data["lang"]
        lang_count = lang_data["count"]
        top_langs_text += f"  • <code>{lang_code}</code>: {fmt(lang_count)}\n"

    paid_pct = stats.get("paid_users_percent", 0)

    text = (
        f"📊 <b>{t('admin_stats_title', lang)}</b>\n\n"
        f"👥 <b>{t('admin_users', lang)}</b>\n"
        f"  {t('admin_total_users', lang, total=fmt(stats['total_users']))}\n"
        f"  {t('admin_paid_percent', lang, pct=paid_pct, count=fmt(stats.get('paid_users', 0)))}\n"
        f"  {t('admin_today_users', lang, count=fmt(stats['today_users']))}\n"
        f"  {t('admin_week_users', lang, count=fmt(stats['week_users']))}\n\n"
        f"📋 <b>{t('admin_by_plan', lang)}</b>\n"
        f"{plans_text}"
        f"  {t('admin_active_subs', lang, count=fmt(stats.get('active_subscriptions', 0)))}\n\n"
        f"🌍 <b>{t('admin_translations', lang)}</b>\n"
        f"  {t('admin_total', lang, count=fmt(stats['total_translations']))}\n"
        f"  {t('admin_today', lang, count=fmt(stats['today_translations']))}\n"
        f"  {t('admin_total_chars', lang, count=fmt(stats['total_chars']))}\n"
        f"  {t('admin_today_chars', lang, count=fmt(stats['today_chars']))}\n\n"
    )

    if top_langs_text:
        text += f"🏆 <b>{t('admin_top_langs', lang)}</b>\n{top_langs_text}"

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu_kb(lang),
        parse_mode="HTML",
    )


async def _fetch_payment_config() -> dict | None:
    """Запрашивает конфиг видимости способов оплаты из API."""
    if not settings.api_url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.api_url}/admin/payment-config",
                headers={"X-Bot-Secret": settings.bot_internal_secret},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("admin/payment-config returned %s", resp.status)
                return None
    except Exception as e:
        logger.warning("admin/payment-config failed: %s", e)
        return None


async def _toggle_payment_method(method: str, visible: bool) -> dict | None:
    """Включает/выключает способ оплаты через API."""
    if not settings.api_url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.api_url}/admin/payment-config",
                headers={"X-Bot-Secret": settings.bot_internal_secret},
                json={"method": method, "visible": visible},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("admin/payment-config POST returned %s", resp.status)
                return None
    except Exception as e:
        logger.warning("admin/payment-config POST failed: %s", e)
        return None


@router.callback_query(F.data == "admin_payment")
async def cb_admin_payment(callback: CallbackQuery) -> None:
    """Показывает настройки видимости способов оплаты."""
    if not _is_admin(callback.from_user.id):
        return
    await callback.answer()
    user = await get_user(callback.from_user.id)

    config = await _fetch_payment_config()
    if not config:
        config = {"stars": True, "kofi": True, "paypal": False, "monobank": False}

    await callback.message.edit_text(
        t("admin_payment_title", user.ui_language),
        reply_markup=admin_payment_kb(config, user.ui_language),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_toggle:"))
async def cb_admin_toggle_method(callback: CallbackQuery) -> None:
    """Включает/выключает способ оплаты."""
    if not _is_admin(callback.from_user.id):
        return
    await callback.answer()
    user = await get_user(callback.from_user.id)

    method = callback.data.split(":", 1)[1]
    if method not in ("stars", "kofi", "paypal", "monobank"):
        return

    # Fetch current config
    config = await _fetch_payment_config()
    if not config:
        config = {"stars": True, "kofi": True, "paypal": False, "monobank": False}

    # Toggle
    new_visible = not config.get(method, True)

    updated = await _toggle_payment_method(method, new_visible)
    if not updated:
        await callback.message.edit_text(
            t("admin_payment_error", user.ui_language),
            reply_markup=admin_payment_kb(config, user.ui_language),
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        t("admin_payment_title", user.ui_language),
        reply_markup=admin_payment_kb(updated, user.ui_language),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery) -> None:
    """Возврат в админ-меню."""
    if not _is_admin(callback.from_user.id):
        return
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"⚙️ <b>{t('admin_panel', user.ui_language)}</b>\n\n"
        f"{t('admin_choose_option', user.ui_language)}:",
        reply_markup=admin_menu_kb(user.ui_language),
        parse_mode="HTML",
    )
    await callback.answer()
