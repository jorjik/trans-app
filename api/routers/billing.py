"""Billing — планы и оформление подписки."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from db.session import get_db
from models import User
from schemas import PlansListResponse, PlanResponse, CheckoutRequest, CheckoutResponse
from services.auth import get_current_user
from services.quota import get_or_create_quota, upgrade_plan

router = APIRouter(prefix="/billing", tags=["billing"])

# Статические данные планов (в production — из БД таблицы plans)
PLANS = [
    PlanResponse(
        id="free",
        name="Free",
        chars_per_month=50_000,
        price_usd=0.0,
        price_stars=0,
        max_auto_chats=2,
        features=["basic_translate", "inline_mode"],
    ),
    PlanResponse(
        id="starter",
        name="Starter",
        chars_per_month=500_000,
        price_usd=4.99,
        price_stars=250,
        max_auto_chats=5,
        features=["basic_translate", "inline_mode", "auto_translate", "stats"],
    ),
    PlanResponse(
        id="pro",
        name="Pro",
        chars_per_month=2_000_000,
        price_usd=14.99,
        price_stars=750,
        max_auto_chats=20,
        features=[
            "basic_translate", "inline_mode", "auto_translate",
            "stats", "priority_support", "deepl_engine",
        ],
    ),
    PlanResponse(
        id="business",
        name="Business",
        chars_per_month=10_000_000,
        price_usd=49.99,
        price_stars=2500,
        max_auto_chats=50,
        features=[
            "basic_translate", "inline_mode", "auto_translate", "stats",
            "priority_support", "deepl_engine", "group_quota", "api_access",
        ],
    ),
]

PLAN_MAP = {p.id: p for p in PLANS}


@router.get("/plans", response_model=PlansListResponse)
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlansListResponse:
    """Список доступных тарифных планов."""
    quota = await get_or_create_quota(db, current_user.id)
    return PlansListResponse(plans=PLANS, current_plan=quota.plan)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """
    Создаёт платёжную сессию.
    MVP: Telegram Stars — возвращает ссылку на invoice.
    Stripe/ЮKassa — будет добавлено в v2.
    """
    if body.plan_id not in PLAN_MAP:
        raise AppError(
            status_code=422,
            error="invalid_plan",
            message=f"Unknown plan: {body.plan_id}",
        )

    plan = PLAN_MAP[body.plan_id]

    if body.payment_method == "telegram_stars":
        # MVP: формируем ссылку на invoice через бота
        # В production бот создаёт настоящий invoice через sendInvoice
        invoice_url = (
            f"https://t.me/transappbot?start=pay_{body.plan_id}"
            f"_{current_user.id}"
        )
    elif body.payment_method in ("stripe", "yookassa"):
        raise AppError(
            status_code=501,
            error="not_implemented",
            message=f"{body.payment_method} integration coming in v2",
        )
    else:
        raise AppError(
            status_code=422,
            error="invalid_payment_method",
            message=f"Unknown payment method: {body.payment_method}",
        )

    return CheckoutResponse(
        invoice_url=invoice_url,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@router.post("/webhook/stars", include_in_schema=False)
async def stars_webhook(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Вызывается после успешной оплаты через Telegram Stars.
    В production — вызывается ботом при successful_payment апдейте.
    """
    # TODO: верифицировать платёж, получить plan_id из payload
    # await upgrade_plan(db, current_user.id, plan_id)
    return {"status": "ok"}
