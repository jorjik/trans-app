"""GET /plans, POST /billing/checkout."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter

from dependencies import CurrentUser, DB
from schemas import PlansListResponse, PlanResponse, CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    PlanResponse(id="free",     name="Free",     chars_per_month=50_000,     price_usd=0,     price_stars=0,    max_auto_chats=2,  features=["basic_translate", "inline_mode"]),
    PlanResponse(id="starter",  name="Starter",  chars_per_month=500_000,    price_usd=4.99,  price_stars=250,  max_auto_chats=5,  features=["basic_translate", "inline_mode", "auto_translate", "stats"]),
    PlanResponse(id="pro",      name="Pro",       chars_per_month=2_000_000,  price_usd=14.99, price_stars=750,  max_auto_chats=20, features=["basic_translate", "inline_mode", "auto_translate", "stats", "gpt_engine"]),
    PlanResponse(id="business", name="Business",  chars_per_month=10_000_000, price_usd=49.99, price_stars=2500, max_auto_chats=50, features=["basic_translate", "inline_mode", "auto_translate", "stats", "gpt_engine", "group_quota"]),
]


@router.get("/plans", response_model=PlansListResponse)
async def get_plans() -> PlansListResponse:
    return PlansListResponse(plans=PLANS)


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(body: CheckoutRequest, user: CurrentUser, db: DB) -> CheckoutResponse:
    # Р’ MVP: РІРѕР·РІСЂР°С‰Р°РµРј Р·Р°РіР»СѓС€РєСѓ, РїРѕР»РЅР°СЏ РёРЅС‚РµРіСЂР°С†РёСЏ вЂ” v2
    # Р—РґРµСЃСЊ Р±СѓРґРµС‚: СЃРѕР·РґР°РЅРёРµ invoice С‡РµСЂРµР· Telegram Stars РёР»Рё Stripe
    plan = next((p for p in PLANS if p.id == body.plan_id), None)
    if not plan:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Plan not found")

    # TODO: СЃРѕР·РґР°С‚СЊ СЂРµР°Р»СЊРЅС‹Р№ invoice
    invoice_url = f"https://t.me/transappbot?start=pay_{body.plan_id}_{user.id}"

    return CheckoutResponse(
        invoice_url=invoice_url,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )