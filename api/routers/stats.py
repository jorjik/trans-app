"""GET /stats/me — статистика переводов пользователя."""

from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models import TranslationLog, User
from schemas import StatsResponse, DayStats, LangStats
from services.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=StatsResponse)
async def get_my_stats(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    """Статистика за последние N дней."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Все логи за период
    result = await db.execute(
        select(TranslationLog)
        .where(
            TranslationLog.user_id == current_user.id,
            TranslationLog.created_at >= since,
            TranslationLog.status == "success",
        )
        .order_by(TranslationLog.created_at)
    )
    logs = result.scalars().all()

    # Агрегация по дням
    by_day: dict[str, int] = defaultdict(int)
    by_lang: dict[str, int] = defaultdict(int)
    by_provider: dict[str, int] = defaultdict(int)
    total_chars = 0
    total_requests = 0

    for log in logs:
        total_chars += log.char_count or 0
        total_requests += 1

        day_key = log.created_at.strftime("%Y-%m-%d")
        by_day[day_key] += log.char_count or 0

        if log.target_lang:
            by_lang[log.target_lang] += log.char_count or 0

        if log.provider:
            by_provider[log.provider] += 1

    # Заполняем пропущенные дни нулями
    chars_by_day = []
    for i in range(days):
        d = (since + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        chars_by_day.append(DayStats(date=d, chars=by_day.get(d, 0)))

    top_langs = sorted(
        [LangStats(lang=k, chars=v) for k, v in by_lang.items()],
        key=lambda x: x.chars,
        reverse=True,
    )[:10]

    return StatsResponse(
        period=f"{days}d",
        total_chars=total_chars,
        total_requests=total_requests,
        chars_by_day=chars_by_day,
        top_languages=top_langs,
        providers_used={
            "google_free": by_provider.get("google_free", 0),
            "deepl": by_provider.get("deepl", 0),
            "openai": by_provider.get("openai", 0),
        },
    )
