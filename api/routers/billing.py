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
from models import BillingEvent, User
from schemas import (
    PlansListResponse,
    PlanResponse,
    CheckoutRequest,
    CheckoutResponse,
    StarsInternalPayment,
)
from services.auth import get_current_user
from services.billing_plans import PLAN_CATALOG
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
