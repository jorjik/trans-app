"""POST /translate — основной эндпоинт перевода."""

import logging
import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import RateLimitError, TranslationError
from db.session import get_db
from models import TranslationLog, User
from schemas import TranslateRequest, TranslateResponse
from services.auth import get_current_user
from services.cache import check_rate_limit
from services.quota import check_quota, deduct_chars, get_or_create_quota
from services.translation import router as tr

log = logging.getLogger(__name__)
router = APIRouter(prefix="/translate", tags=["translate"])


@router.post("", response_model=TranslateResponse)
async def do_translate(
    body: TranslateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TranslateResponse:
    """Переводит текст. Кэшированные переводы символы НЕ списывают."""

    if not await check_rate_limit(current_user.id):
        raise RateLimitError(retry_after=1)

    text = body.text.strip()
    char_count = len(text)

    # Проверяем квоту (выбрасывает QuotaExceededError если нет баланса)
    await check_quota(db, current_user.id, char_count)

    t0 = time.monotonic()
    status = "success"
    error_code = None
    result = None

    try:
        result = await tr.translate(
            text=text,
            target_lang=body.target_lang,
            source_lang=body.source_lang,
            engine=body.engine,
        )
    except ValueError as e:
        status, error_code = "error", "unsupported_language"
        raise TranslationError(str(e))
    except RuntimeError as e:
        status, error_code = "error", "provider_error"
        log.error("Translation failed: %s", e)
        raise TranslationError("Translation service temporarily unavailable")
    finally:
        latency_ms = int((time.monotonic() - t0) * 1000)
        db.add(TranslationLog(
            user_id=current_user.id,
            source_lang=result.source_lang if result else body.source_lang,
            target_lang=body.target_lang,
            char_count=char_count,
            provider=result.provider if result else None,
            latency_ms=latency_ms,
            cached=result.cached if result else False,
            status=status,
            error_code=error_code,
        ))

    if not result.cached:
        quota = await deduct_chars(db, current_user.id, char_count)
    else:
        quota = await get_or_create_quota(db, current_user.id)

    return TranslateResponse(
        translated_text=result.translated_text,
        source_lang_detected=result.source_lang,
        target_lang=result.target_lang,
        provider=result.provider,
        cached=result.cached,
        char_count=char_count,
        chars_remaining=quota.chars_remaining,
    )
