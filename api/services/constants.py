"""Shared constants — единый источник правды для лимитов тарифов."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanInfo:
    id: str
    name: str
    chars_limit: int
    stars: int | None = None  # Telegram Stars цена; None = бесплатный


# Единый источник правды
PLANS: dict[str, PlanInfo] = {
    "free":     PlanInfo("free",     "Free",     50_000),
    "starter":  PlanInfo("starter",  "Starter",  500_000,   250),
    "pro":      PlanInfo("pro",      "Pro",      2_000_000, 750),
    "business": PlanInfo("business", "Business", 10_000_000, 2500),
}

PLAN_LIMITS: dict[str, int] = {p.id: p.chars_limit for p in PLANS.values()}

MAX_CHATS_BY_PLAN: dict[str, int] = {
    "free":     2,
    "starter":  5,
    "pro":      20,
    "business": 50,
}
