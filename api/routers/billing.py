"""Billing — планы, checkout Stars, внутренний webhook от бота."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.errors import AppError, UnauthorizedError
from db.session import get_db
from models import BillingEvent, PaymentIntent, User
from schemas import (
    PlansListResponse,
    PlanResponse,
    CheckoutRequest,
    CheckoutResponse,
    StarsInternalPayment,
)
from services.auth import get_current_user
from services.billing_plans import PLAN_CATALOG
from services.constants import PLANS
from services.kofi import amount_for_plan as kofi_amount_for_plan
from routers.kofi import generate_kofi_code as _gen_kofi_code
from services.paypal import PayPalClient
from services.quota import get_or_create_quota, upgrade_plan
from services.telegram_stars import create_stars_invoice_link

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


def _plan_to_response(item) -> PlanResponse:
    return PlanResponse(
        id=item.id,
        name=item.name,
        chars_per_month=item.chars_per_month,
        price_usd=item.price_usd,
        price_stars=item.price_stars,
        max_auto_chats=item.max_auto_chats,
        features=list(item.features),
    )


PLANS = [_plan_to_response(p) for p in PLAN_CATALOG.values()]
PLAN_MAP = {p.id: p for p in PLANS}


@router.get("/plans", response_model=PlansListResponse)
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlansListResponse:
    quota = await get_or_create_quota(db, current_user.id)
    return PlansListResponse(plans=PLANS, current_plan=quota.plan)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
) -> CheckoutResponse:
    """Создаёт ссылку на оплату Telegram Stars (createInvoiceLink)."""
    if body.plan_id not in PLAN_CATALOG:
        raise AppError(
            status_code=422,
            error="invalid_plan",
            message=f"Unknown plan: {body.plan_id}",
        )

    if body.payment_method != "telegram_stars":
        raise AppError(
            status_code=501,
            error="not_implemented",
            message=f"{body.payment_method} integration coming in v2",
        )

    invoice_url = await create_stars_invoice_link(
        plan_id=body.plan_id,
        telegram_id=current_user.telegram_id,
    )

    return CheckoutResponse(
        invoice_url=invoice_url,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@router.post("/internal/stars", include_in_schema=False)
async def internal_stars_payment(
    body: StarsInternalPayment,
    x_billing_secret: Annotated[str | None, Header(alias="X-Billing-Secret")] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Вызывается ботом после successful_payment.
    Требует BOT_WEBHOOK_SECRET в заголовке X-Billing-Secret.
    """
    if not settings.bot_webhook_secret:
        raise AppError(
            status_code=503,
            error="billing_secret_not_configured",
            message="BOT_WEBHOOK_SECRET is not set on API",
        )

    if x_billing_secret != settings.bot_webhook_secret:
        raise UnauthorizedError("Invalid billing secret")

    if body.plan_id not in PLAN_CATALOG or body.plan_id == "free":
        raise AppError(
            status_code=422,
            error="invalid_plan",
            message=f"Unknown plan: {body.plan_id}",
        )

    result = await db.execute(
        select(User).where(User.telegram_id == body.telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AppError(
            status_code=404,
            error="user_not_found",
            message="User not found for telegram_id",
        )

    existing_payment = await db.execute(
        select(BillingEvent).where(
            BillingEvent.provider_charge_id == body.telegram_payment_charge_id
        )
    )
    payment = existing_payment.scalar_one_or_none()
    if payment:
        return {"status": "ok", "plan": payment.plan_id, "user_id": payment.user_id}

    db.add(
        BillingEvent(
            user_id=user.id,
            provider="telegram_stars",
            provider_charge_id=body.telegram_payment_charge_id,
            plan_id=body.plan_id,
            amount=body.total_amount,
        )
    )

    await upgrade_plan(db, user.id, body.plan_id)
    log.info(
        "Stars payment applied user_id=%s plan=%s charge=%s",
        user.id,
        body.plan_id,
        body.telegram_payment_charge_id,
    )

    return {"status": "ok", "plan": body.plan_id, "user_id": user.id}


@router.post("/intent", response_model=dict)
async def create_payment_intent(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Создаёт платёжное намерение для Ko-fi."""
    if body.plan_id not in PLAN_CATALOG:
        raise AppError(
            status_code=422,
            error="invalid_plan",
            message=f"Unknown plan: {body.plan_id}",
        )

    plan_info = PLAN_CATALOG[body.plan_id]
    if plan_info.price_stars <= 0:
        raise AppError(
            status_code=422,
            error="free_plan",
            message="Free plan cannot be purchased",
        )

    if body.payment_method == "kofi":
        code = _gen_kofi_code(current_user.id, body.plan_id)
        amount = kofi_amount_for_plan(plan_info.price_stars, settings.kofi_amount_per_star)
        db.add(PaymentIntent(
            user_id=current_user.id,
            provider="kofi",
            plan_id=body.plan_id,
            code=code,
            amount=amount,
            currency=settings.kofi_currency,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
        await db.flush()
        return {
            "provider": "kofi",
            "code": code,
            "amount": amount,
            "currency": settings.kofi_currency,
            "page_url": settings.kofi_page_url or "",
        }
    else:
        raise AppError(
            status_code=501,
            error="not_implemented",
            message=f"{body.payment_method} payment intent coming soon",
        )


paypal_client_inst = PayPalClient()


@router.post("/paypal/create-order", response_model=dict)
async def paypal_create_order(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Создаёт PayPal заказ для оплаты тарифа."""
    if body.plan_id not in PLAN_CATALOG:
        raise AppError(status_code=422, error="invalid_plan", message=f"Unknown plan: {body.plan_id}")

    plan_info = PLAN_CATALOG[body.plan_id]
    if plan_info.price_stars <= 0:
        raise AppError(status_code=422, error="free_plan", message="Free plan cannot be purchased")

    amount = kofi_amount_for_plan(plan_info.price_stars, settings.paypal_amount_per_star)
    reference_id = f"user_{current_user.id}_plan_{body.plan_id}"

    order = await paypal_client_inst.create_order(
        amount=amount,
        currency=settings.paypal_currency,
        reference_id=reference_id,
    )

    if not order:
        raise AppError(
            status_code=502,
            error="paypal_error",
            message=paypal_client_inst.last_error or "Failed to create PayPal order",
        )

    order_id = order["id"]
    approval_url = next(
        (link["href"] for link in order.get("links", []) if link.get("rel") == "approve"),
        None,
    )

    # Сохраняем намерение
    db.add(PaymentIntent(
        user_id=current_user.id,
        provider="paypal",
        plan_id=body.plan_id,
        code=order_id,
        amount=amount,
        currency=settings.paypal_currency,
        external_id=order_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=3),
    ))
    await db.flush()

    return {
        "provider": "paypal",
        "order_id": order_id,
        "approval_url": approval_url or "",
        "amount": amount,
        "currency": settings.paypal_currency,
    }


@router.post("/paypal/capture/{order_id}", response_model=dict)
async def paypal_capture_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Захватывает PayPal заказ после подтверждения пользователем."""
    # Проверяем намерение
    result = await db.execute(
        select(PaymentIntent).where(
            PaymentIntent.code == order_id,
            PaymentIntent.user_id == current_user.id,
            PaymentIntent.provider == "paypal",
        )
    )
    intent = result.scalar_one_or_none()
    if not intent:
        raise AppError(status_code=404, error="intent_not_found", message="Payment intent not found")

    if intent.status == "paid":
        return {"status": "already_paid", "plan": intent.plan_id}

    if intent.status in ("expired", "cancelled"):
        raise AppError(status_code=400, error="intent_expired", message="Payment session expired")

    # Захватываем
    capture = await paypal_client_inst.capture_order(order_id)
    if not capture:
        raise AppError(
            status_code=502,
            error="paypal_error",
            message=paypal_client_inst.last_error or "Failed to capture PayPal order",
        )

    if capture.get("status") != "COMPLETED":
        # Может быть APPROVED — пользователь ещё не подтвердил
        return {"status": capture.get("status", "unknown"), "order_id": order_id}

    # Получаем ID захвата
    capture_id = ""
    purchase_units = capture.get("purchase_units") or []
    if purchase_units:
        captures = purchase_units[0].get("payments", {}).get("captures") or []
        if captures:
            capture_id = captures[0].get("id", "")

    # Помечаем как оплаченный
    intent.status = "paid"
    intent.external_id = capture_id

    # Записываем в BillingEvent
    db.add(BillingEvent(
        user_id=current_user.id,
        provider="paypal",
        provider_charge_id=capture_id or order_id,
        plan_id=intent.plan_id,
        amount=0,
    ))

    await upgrade_plan(db, current_user.id, intent.plan_id)
    await db.flush()

    log.info("PayPal payment applied user=%s plan=%s order=%s", current_user.id, intent.plan_id, order_id)

    return {"status": "paid", "plan": intent.plan_id}


@router.get("/paypal/status/{order_id}", response_model=dict)
async def paypal_order_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Проверяет статус PayPal заказа."""
    order = await paypal_client_inst.get_order(order_id)
    if not order:
        raise AppError(
            status_code=502,
            error="paypal_error",
            message=paypal_client_inst.last_error or "Failed to get PayPal order",
        )
    return {"status": order.get("status", "unknown"), "order_id": order_id}
