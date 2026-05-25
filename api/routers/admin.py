"""GET /admin/stats — статистика по всему сервису (только для админов).

Доступ: защищён X-Bot-Secret (как и /internal/*).
Админ проверяется на стороне бота по admin_tg_ids.
"""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.session import get_db
from models import User, TranslationLog, Quota, Subscription

log = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if x_bot_secret != settings.bot_internal_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/stats", dependencies=[Depends(verify_bot_secret)])
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Возвращает общую статистику сервиса (только для админов)."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)

    # ── Total users ──
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # ── Paid users count (all non-free plans) ──
    paid_users_result = await db.execute(
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(Quota, User.id == Quota.user_id)
        .where(Quota.plan != "free")
    )
    paid_users = paid_users_result.scalar() or 0
    paid_users_percent = round(paid_users / total_users * 100, 1) if total_users > 0 else 0.0

    # ── Users created today ──
    today_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    today_users = today_users_result.scalar() or 0

    # ── Users created this week ──
    week_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    week_users = week_users_result.scalar() or 0

    # ── Users by plan (via quotas) ──
    plan_result = await db.execute(
        select(Quota.plan, func.count(Quota.id))
        .group_by(Quota.plan)
    )
    users_by_plan = dict(plan_result.all())

    # ── Total translations ──
    total_translations_result = await db.execute(
        select(func.count(TranslationLog.id))
        .where(TranslationLog.status == "success")
    )
    total_translations = total_translations_result.scalar() or 0

    # ── Translations today ──
    today_translations_result = await db.execute(
        select(func.count(TranslationLog.id))
        .where(
            TranslationLog.status == "success",
            TranslationLog.created_at >= today_start,
        )
    )
    today_translations = today_translations_result.scalar() or 0

    # ── Chars translated total ──
    total_chars_result = await db.execute(
        select(func.coalesce(func.sum(TranslationLog.char_count), 0))
        .where(TranslationLog.status == "success")
    )
    total_chars = total_chars_result.scalar() or 0

    # ── Chars today ──
    today_chars_result = await db.execute(
        select(func.coalesce(func.sum(TranslationLog.char_count), 0))
        .where(
            TranslationLog.status == "success",
            TranslationLog.created_at >= today_start,
        )
    )
    today_chars = today_chars_result.scalar() or 0

    # ── Active subscriptions ──
    active_subs_result = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status == "active")
    )
    active_subs = active_subs_result.scalar() or 0

    # ── Top target languages (all time) ──
    top_langs_result = await db.execute(
        select(
            TranslationLog.target_lang,
            func.count(TranslationLog.id).label("count"),
        )
        .where(
            TranslationLog.status == "success",
            TranslationLog.target_lang.isnot(None),
        )
        .group_by(TranslationLog.target_lang)
        .order_by(func.count(TranslationLog.id).desc())
        .limit(5)
    )
    top_languages = [
        {"lang": row[0], "count": row[1]}
        for row in top_langs_result.all()
    ]

    return {
        "total_users": total_users,
        "today_users": today_users,
        "week_users": week_users,
        "users_by_plan": users_by_plan,
        "paid_users": paid_users,
        "paid_users_percent": paid_users_percent,
        "total_translations": total_translations,
        "today_translations": today_translations,
        "total_chars": total_chars,
        "today_chars": today_chars,
        "active_subscriptions": active_subs,
        "top_languages": top_languages,
    }
