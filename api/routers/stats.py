"""GET /stats/me вЂ” СЃС‚Р°С‚РёСЃС‚РёРєР° РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ."""

from datetime import datetime, timezone, timedelta
from collections import defaultdict

from fastapi import APIRouter
from sqlalchemy import select

from dependencies import CurrentUser, DB
from models import TranslationLog
from schemas import StatsResponse, DailyStats, LangStats, ProviderStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=StatsResponse)
async def get_stats(user: CurrentUser, db: DB) -> StatsResponse:
    since = datetime.now(timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(TranslationLog)
        .where(
            TranslationLog.user_id == user.id,
            TranslationLog.created_at >= since,
            TranslationLog.status == "success",
        )
        .order_by(TranslationLog.created_at)
    )
    logs = result.scalars().all()

    total_chars = sum(l.char_count for l in logs)
    total_requests = len(logs)

    # By day
    by_day: dict[str, int] = defaultdict(int)
    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        by_day[day] += log.char_count

    # By language
    by_lang: dict[str, int] = defaultdict(int)
    for log in logs:
        if log.target_lang:
            by_lang[log.target_lang] += log.char_count

    # By provider
    by_provider: dict[str, int] = defaultdict(int)
    for log in logs:
        if log.provider:
            by_provider[log.provider] += 1

    return StatsResponse(
        period="30d",
        total_chars=total_chars,
        total_requests=total_requests,
        chars_by_day=[DailyStats(date=d, chars=c) for d, c in sorted(by_day.items())],
        top_languages=sorted(
            [LangStats(lang=l, chars=c) for l, c in by_lang.items()],
            key=lambda x: x.chars, reverse=True,
        )[:5],
        providers_used=ProviderStats(
            google=by_provider.get("google", 0),
            deepl=by_provider.get("deepl", 0),
            openai=by_provider.get("openai", 0),
            google_free=by_provider.get("google_free", 0),
        ),
    )