"""Оплата Telegram Stars — invoice, pre_checkout, successful_payment."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from services.billing import (
    get_plan,
    notify_api_stars_paid,
    parse_payload,
    start_checkout,
)
from services.storage import upgrade_plan, get_user
from utils.i18n import t

log = logging.getLogger(__name__)
router = Router(name="billing")


@router.callback_query(F.data.startswith("upgrade:"))
async def cb_upgrade_plan(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    plan_id = callback.data.split(":", 1)[1]
    await callback.answer()
    try:
        await start_checkout(callback.message, plan_id)
    except Exception:
        log.exception("Failed to send invoice plan=%s", plan_id)
        await callback.message.answer(t("billing_invoice_error", user.ui_language))


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    user = get_user(query.from_user.id)
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
    user = get_user(message.from_user.id)
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
    upgraded_user = upgrade_plan(telegram_id, plan_id)
    synced = await notify_api_stars_paid(
        telegram_id=telegram_id,
        plan_id=plan_id,
        charge_id=payment.telegram_payment_charge_id,
        total_amount=payment.total_amount,
    )

    sync_note = t("billing_sync_note", user.ui_language) if not synced else ""

    # Используем ui_language из обновлённого пользователя
    lang = upgraded_user.ui_language
    await message.answer(
        t("billing_success_activated", lang,
            plan=plan.name,
            limit=upgraded_user.chars_limit,
            remaining=upgraded_user.chars_remaining,
            sync_note=sync_note,
        ),
        parse_mode="HTML",
    )
