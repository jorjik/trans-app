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
from services.storage import upgrade_plan

log = logging.getLogger(__name__)
router = Router(name="billing")


@router.callback_query(F.data.startswith("upgrade:"))
async def cb_upgrade_plan(callback: CallbackQuery) -> None:
    plan_id = callback.data.split(":", 1)[1]
    await callback.answer()
    try:
        await start_checkout(callback.message, plan_id)
    except Exception:
        log.exception("Failed to send invoice plan=%s", plan_id)
        await callback.message.answer("❌ Не удалось создать счёт. Попробуй позже.")


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    parsed = parse_payload(query.invoice_payload or "")
    if not parsed:
        await query.answer(ok=False, error_message="Некорректный счёт. Начни оплату заново.")
        return

    plan_id, telegram_id = parsed
    if telegram_id != query.from_user.id:
        await query.answer(ok=False, error_message="Счёт выписан другому пользователю.")
        return

    plan = get_plan(plan_id)
    if not plan:
        await query.answer(ok=False, error_message="Тариф недоступен.")
        return

    if query.currency != "XTR" or query.total_amount != plan.stars:
        await query.answer(ok=False, error_message="Сумма счёта не совпадает с тарифом.")
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    parsed = parse_payload(payment.invoice_payload)
    if not parsed:
        log.warning("successful_payment with bad payload: %s", payment.invoice_payload)
        await message.answer("✅ Оплата получена, но тариф не активирован. Напиши в поддержку.")
        return

    plan_id, telegram_id = parsed
    if telegram_id != message.from_user.id:
        await message.answer("❌ Ошибка привязки платежа.")
        return

    plan = get_plan(plan_id)
    if not plan:
        await message.answer("❌ Тариф не найден после оплаты.")
        return

    user = upgrade_plan(telegram_id, plan_id)
    synced = await notify_api_stars_paid(
        telegram_id=telegram_id,
        plan_id=plan_id,
        charge_id=payment.telegram_payment_charge_id,
        total_amount=payment.total_amount,
    )

    sync_note = "" if synced else "\n\n<i>Mini App обновится после перезапуска, если API недоступен.</i>"
    await message.answer(
        f"✅ Тариф <b>{plan.name}</b> активирован!\n\n"
        f"Лимит: <b>{user.chars_limit:,}</b> символов/мес\n"
        f"Осталось: <b>{user.chars_remaining:,}</b> символов"
        f"{sync_note}",
        parse_mode="HTML",
    )
