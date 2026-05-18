"""Каталог тарифов для Stars (единый источник для API)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanCatalogItem:
    id: str
    name: str
    chars_per_month: int
    price_usd: float
    price_stars: int
    max_auto_chats: int
    features: tuple[str, ...]


PLAN_CATALOG: dict[str, PlanCatalogItem] = {
    "free": PlanCatalogItem(
        id="free",
        name="Free",
        chars_per_month=50_000,
        price_usd=0.0,
        price_stars=0,
        max_auto_chats=2,
        features=("basic_translate", "inline_mode"),
    ),
    "starter": PlanCatalogItem(
        id="starter",
        name="Starter",
        chars_per_month=500_000,
        price_usd=4.99,
        price_stars=250,
        max_auto_chats=5,
        features=("basic_translate", "inline_mode", "auto_translate", "stats"),
    ),
    "pro": PlanCatalogItem(
        id="pro",
        name="Pro",
        chars_per_month=2_000_000,
        price_usd=14.99,
        price_stars=750,
        max_auto_chats=20,
        features=(
            "basic_translate",
            "inline_mode",
            "auto_translate",
            "stats",
            "priority_support",
            "deepl_engine",
        ),
    ),
    "business": PlanCatalogItem(
        id="business",
        name="Business",
        chars_per_month=10_000_000,
        price_usd=49.99,
        price_stars=2500,
        max_auto_chats=50,
        features=(
            "basic_translate",
            "inline_mode",
            "auto_translate",
            "stats",
            "priority_support",
            "deepl_engine",
            "group_quota",
            "api_access",
        ),
    ),
}


def build_invoice_payload(plan_id: str, telegram_id: int) -> str:
    return f"pay:{plan_id}:{telegram_id}"


def parse_invoice_payload(payload: str) -> tuple[str, int] | None:
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "pay":
        return None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None
