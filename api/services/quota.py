"""Управление квотами символов."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Quota, User
from core.errors import QuotaExceededError

logger = logging.getLogger(__name__)

PLAN_LIMITS = {
    "free":     50_000,
    "starter":  500_000,
    "pro":      2_000_000,
    "business": 10_000_000,
}

PLAN_MAX_CHATS = {
    "free": 2,
    "starter": 5,
    "pro": 20,
    "business": 50,
}


async def get_or_create_quota(db: AsyncSession, user_id: int) -> Quota:
    """Возвращает квоту пользователя, создаёт если не существует."""
    result = await db.execute(select(Quota).where(Quota.user_id == user_id))
    quota = result.scalar_one_or_none()

    if not quota:
        quota = Quota(
            user_id=user_id,
            plan="free",
            chars_limit=PLAN_LIMITS["free"],
            chars_used=0,
            reset_at=_next_reset(),
        )
        db.add(quota)
        await db.flush()

    # Сбрасываем если пришло время
    if quota.reset_at and datetime.now(timezone.utc) >= quota.reset_at:
        quota = await _reset_quota(db, quota)

    return quota


async def check_quota(db: AsyncSession, user_id: int, char_count: int) -> Quota:
    """
    Проверяет что у пользователя достаточно символов.
    Выбрасывает QuotaExceededError если лимит исчерпан.
    """
    quota = await get_or_create_quota(db, user_id)

    if quota.chars_used + char_count > quota.chars_limit:
        raise QuotaExceededError(
            chars_used=quota.chars_used,
            chars_limit=quota.chars_limit,
            reset_at=quota.reset_at,
        )

    return quota


async def deduct_chars(db: AsyncSession, user_id: int, char_count: int) -> Quota:
    """Списывает символы с баланса. Возвращает обновлённую квоту."""
    quota = await get_or_create_quota(db, user_id)
    quota.chars_used = min(quota.chars_used + char_count, quota.chars_limit)
    await db.flush()
    return quota


async def add_chars(db: AsyncSession, user_id: int, char_count: int, reason: str = "") -> Quota:
    """Пополняет баланс (реферал, апгрейд)."""
    quota = await get_or_create_quota(db, user_id)
    quota.chars_limit += char_count
    logger.info("Added %d chars to user %d (%s)", char_count, user_id, reason)
    await db.flush()
    return quota


async def upgrade_plan(db: AsyncSession, user_id: int, plan: str) -> Quota:
    """Обновляет план пользователя."""
    if plan not in PLAN_LIMITS:
        raise ValueError(f"Unknown plan: {plan}")

    quota = await get_or_create_quota(db, user_id)
    quota.plan = plan
    quota.chars_limit = PLAN_LIMITS[plan]
    quota.reset_at = _next_reset()
    await db.flush()
    return quota


async def _reset_quota(db: AsyncSession, quota: Quota) -> Quota:
    """Сбрасывает счётчик использования."""
    quota.chars_used = 0
    quota.reset_at = _next_reset()
    logger.info("Quota reset for user %d (plan: %s)", quota.user_id, quota.plan)
    await db.flush()
    return quota


def _next_reset() -> datetime:
    """Следующий сброс — 1-е число следующего месяца в 00:00 UTC."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        return now.replace(year=now.year + 1, month=1, day=1,
                           hour=0, minute=0, second=0, microsecond=0)
    return now.replace(month=now.month + 1, day=1,
                       hour=0, minute=0, second=0, microsecond=0)


def get_max_chats(plan: str) -> int:
    return PLAN_MAX_CHATS.get(plan, 2)
