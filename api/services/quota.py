"""
Quota service — управление балансом символов.
Списание, пополнение, проверка, сброс по расписанию.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Quota
from core.config import settings
from core.errors import QuotaExceededError

log = logging.getLogger(__name__)

from services.constants import PLAN_LIMITS, MAX_CHATS_BY_PLAN


def _next_reset() -> datetime:
    """Первое число следующего месяца в UTC."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        return now.replace(year=now.year + 1, month=1, day=1,
                           hour=0, minute=0, second=0, microsecond=0)
    return now.replace(month=now.month + 1, day=1,
                       hour=0, minute=0, second=0, microsecond=0)


async def get_or_create_quota(db: AsyncSession, user_id: int) -> Quota:
    """Возвращает квоту пользователя, создаёт если не существует."""
    result = await db.execute(select(Quota).where(Quota.user_id == user_id))
    quota = result.scalar_one_or_none()

    if quota is None:
        quota = Quota(
            user_id=user_id,
            plan="free",
            chars_limit=settings.free_plan_chars,
            chars_used=0,
            reset_at=_next_reset(),
        )
        db.add(quota)
        await db.flush()
        log.info("Created quota for user %s", user_id)

    return quota


async def _get_or_create_quota_for_update(db: AsyncSession, user_id: int) -> Quota:
    await get_or_create_quota(db, user_id)
    result = await db.execute(
        select(Quota)
        .where(Quota.user_id == user_id)
        .with_for_update()
    )
    return result.scalar_one()


def _reset_quota_if_needed(quota: Quota) -> None:
    if quota.reset_at and datetime.now(timezone.utc) >= quota.reset_at:
        quota.chars_used = 0
        quota.reset_at = _next_reset()
        log.info("Auto-reset quota for user %s", quota.user_id)


async def check_quota(db: AsyncSession, user_id: int, char_count: int) -> Quota:
    """
    Проверяет, достаточно ли символов.
    Выбрасывает QuotaExceededError если нет.
    Автоматически сбрасывает если прошёл месяц.
    """
    quota = await get_or_create_quota(db, user_id)
    _reset_quota_if_needed(quota)

    if quota.chars_used + char_count > quota.chars_limit:
        raise QuotaExceededError(
            chars_used=quota.chars_used,
            chars_limit=quota.chars_limit,
            reset_at=quota.reset_at,
        )

    return quota


async def deduct_chars(db: AsyncSession, user_id: int, char_count: int) -> Quota:
    """Списывает символы с баланса (вызывать ПОСЛЕ успешного перевода)."""
    quota = await _get_or_create_quota_for_update(db, user_id)
    _reset_quota_if_needed(quota)

    if quota.chars_used + char_count > quota.chars_limit:
        raise QuotaExceededError(
            chars_used=quota.chars_used,
            chars_limit=quota.chars_limit,
            reset_at=quota.reset_at,
        )

    quota.chars_used += char_count
    await db.flush()
    return quota


async def add_chars(db: AsyncSession, user_id: int, char_count: int, reason: str = "") -> Quota:
    """Пополняет баланс (рефералы, промо)."""
    quota = await get_or_create_quota(db, user_id)
    quota.chars_limit += char_count
    log.info("Added %d chars to user %s (reason: %s)", char_count, user_id, reason)
    await db.flush()
    return quota


async def upgrade_plan(
    db: AsyncSession,
    user_id: int,
    plan: str,
) -> Quota:
    """Апгрейд плана — обновляет лимит и план."""
    if plan not in PLAN_LIMITS:
        raise ValueError(f"Unknown plan: {plan}")

    quota = await get_or_create_quota(db, user_id)
    quota.plan = plan
    quota.chars_limit = PLAN_LIMITS[plan]
    quota.reset_at = _next_reset()
    log.info("Upgraded user %s to plan %s", user_id, plan)
    await db.flush()
    return quota


def get_max_chats(plan: str) -> int:
    return MAX_CHATS_BY_PLAN.get(plan, 2)
