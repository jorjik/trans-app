"""Оплата — Telegram Stars, Ko-fi, PayPal."""

import logging

import aiohttp
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from config import settings
from keyboards.inline_kb import (
    billing_methods_kb,
    kofi_payment_kb,
    paypal_payment_kb,
)
from services.billing import (
    get_plan,
    notify_api_stars_paid,
    parse_payload,
    start_checkout,
    create_kofi_intent,
    create_paypal_order,
    capture_paypal_order,
    get_paypal_order_status,
)
from services.storage import upgrade_plan, get_user
from utils.i18n import t

log = logging.getLogger(__name__)
router = Router(name="billing")


default_visible = {"stars": True, "kofi": True, "paypal": True}


async def _get_visible_payment_methods() -> dict:
    """Запрашивает из API, какие способы оплаты видны пользователям.
    При ошибке возвращает всё."""
    if not settings.api_url:
        return default_visible
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.api_url}/admin/payment-config",
                headers={"X-Bot-Secret": settings.bot_internal_secret},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        log.warning("Failed to fetch payment config")
    return default_visible


@router.callback_query(F.data.startswith("upgrade:"))
async def cb_upgrade_plan(callback: CallbackQuery) -> None:
    """Показывает выбор способа оплаты для тарифа."""
    plan_id = callback.data.split(":", 1)[1]
    user = await get_user(callback.from_user.id)
    await callback.answer()
    plan = get_plan(plan_id)
    if not plan:
        await callback.message.answer(t("billing_invoice_error", user.ui_language))
        return

    visible = await _get_visible_payment_methods()

    await callback.message.edit_text(
        t("billing_choose_method", user.ui_language,
          plan=plan.name, price_stars=plan.stars),
        reply_markup=billing_methods_kb(plan_id, user.ui_language, visible=visible),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("pay_stars:"))
async def cb_pay_stars(callback: CallbackQuery) -> None:
    """Оплата через Telegram Stars."""
    plan_id = callback.data.split(":", 1)[1]
    user = await get_user(callback.from_user.id)
    await callback.answer()
    try:
        await start_checkout(callback.message, plan_id)
    except Exception:
        log.exception("Failed to send invoice plan=%s", plan_id)
        await callback.message.answer(t("billing_invoice_error", user.ui_language))


@router.callback_query(F.data.startswith("pay_kofi:"))
async def cb_pay_kofi(callback: CallbackQuery) -> None:
    """Оплата через Ko-fi."""
    plan_id = callback.data.split(":", 1)[1]
    user = await get_user(callback.from_user.id)
    await callback.answer()

    result = await create_kofi_intent(callback.from_user.id, plan_id)
    if not result:
        await callback.message.edit_text(
            t("billing_generic_error", user.ui_language),
        )
        return

    code = result.get("code", "")
    amount = result.get("amount", "0.00")
    currency = result.get("currency", "USD")
    page_url = result.get("page_url", "https://ko-fi.com")

    plan = get_plan(plan_id)
    plan_name = plan.name if plan else plan_id.capitalize()

    await callback.message.edit_text(
        t("billing_kofi_instructions", user.ui_language,
          plan=plan_name, amount=amount, currency=currency, code=code),
        reply_markup=kofi_payment_kb(page_url, user.ui_language),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("pay_paypal:"))
async def cb_pay_paypal(callback: CallbackQuery) -> None:
    """Оплата через PayPal."""
    plan_id = callback.data.split(":", 1)[1]
    user = await get_user(callback.from_user.id)
    await callback.answer()

    result = await create_paypal_order(callback.from_user.id, plan_id)
    if not result:
        await callback.message.edit_text(
            t("billing_generic_error", user.ui_language),
        )
        return

    order_id = result.get("order_id", "")
    approval_url = result.get("approval_url", "")
    amount = result.get("amount", "0.00")
    currency = result.get("currency", "USD")

    if not order_id or not approval_url:
        await callback.message.edit_text(
            t("billing_generic_error", user.ui_language),
        )
        return

    plan = get_plan(plan_id)
    plan_name = plan.name if plan else plan_id.capitalize()

    await callback.message.edit_text(
        t("billing_paypal_instructions", user.ui_language,
          plan=plan_name, amount=amount, currency=currency),
        reply_markup=paypal_payment_kb(approval_url, order_id, user.ui_language),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("paypal_check:"))
async def cb_paypal_check(callback: CallbackQuery) -> None:
    """Проверяет статус PayPal заказа и захватывает платеж."""
    order_id = callback.data.split(":", 1)[1]
    user = await get_user(callback.from_user.id)
    await callback.answer()

    status_result = await get_paypal_order_status(callback.from_user.id, order_id)
    if not status_result:
        await callback.message.edit_text(
            t("billing_generic_error", user.ui_language),
        )
        return

    pp_status = status_result.get("status", "")

    if pp_status == "APPROVED":
        # Пользователь подтвердил — захватываем
        cap_result = await capture_paypal_order(callback.from_user.id, order_id)
        if not cap_result or cap_result.get("status") != "paid":
            await callback.message.edit_text(
                t("billing_paypal_error", user.ui_language),
            )
            return

        await callback.message.edit_text(
            t("billing_paypal_success", user.ui_language,
              plan=cap_result.get("plan", "").capitalize()),
            parse_mode="HTML",
        )
    elif pp_status == "COMPLETED":
        # Уже оплачен
        await callback.message.edit_text(
            t("billing_paypal_success", user.ui_language,
              plan=""),
            parse_mode="HTML",
        )
    elif pp_status == "CREATED":
        # Ещё не подтверждён
        await callback.message.edit_text(
            t("billing_paypal_pending", user.ui_language),
            reply_markup=paypal_payment_kb(
                status_result.get("approval_url", ""),
                order_id,
                user.ui_language,
            ),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            t("billing_paypal_error", user.ui_language),
        )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    user = await get_user(query.from_user.id)
    parsed = parse_payload(query.invoice_payload or "")
    if not parsed:
        await query.answer(ok=False, error_message=t("billing_pre_checkout_invalid", user.ui_language))
        return

    plan_id, telegram_id = parsed
    if telegram_id != query.from_user.id:
        await query.answer(ok=False, error_message=t("billing_pre_checkout_wrong_user", user.ui_language))
        return

    plan = get_plan(plan_id)
    if not plan:
        await query.answer(ok=False, error_message=t("billing_pre_checkout_unavailable", user.ui_language))
        return

    if query.currency != "XTR" or query.total_amount != plan.stars:
        await query.answer(ok=False, error_message=t("billing_pre_checkout_wrong_amount", user.ui_language))
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    user = await get_user(message.from_user.id)
    payment = message.successful_payment
    parsed = parse_payload(payment.invoice_payload)
    if not parsed:
        log.warning("successful_payment with bad payload: %s", payment.invoice_payload)
        await message.answer(t("billing_success_fallback", user.ui_language))
        return

    plan_id, telegram_id = parsed
    if telegram_id != message.from_user.id:
        await message.answer(t("billing_success_wrong_user", user.ui_language))
        return

    plan = get_plan(plan_id)
    if not plan:
        await message.answer(t("billing_success_no_plan", user.ui_language))
        return

    # После апгрейда получаем обновлённого пользователя
    await upgrade_plan(telegram_id, plan_id)
    synced = await notify_api_stars_paid(
        telegram_id=telegram_id,
        plan_id=plan_id,
        charge_id=payment.telegram_payment_charge_id,
        total_amount=payment.total_amount,
    )

    sync_note = t("billing_sync_note", user.ui_language) if not synced else ""
    updated_user = await get_user(message.from_user.id)

    await message.answer(
        t("billing_success_activated", updated_user.ui_language,
            plan=plan.name,
            limit=updated_user.chars_limit,
            remaining=updated_user.chars_remaining,
            sync_note=sync_note,
        ),
        parse_mode="HTML",
    )
