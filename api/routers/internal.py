"""Internal API — endpoints для взаимодействия бота с API (защищены общим секретом)."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from core.config import settings
from db.session import get_db
from models import User
from services.quota import get_or_create_quota
from core.security import hash_telegram_id

log = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if x_bot_secret != settings.bot_internal_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


class SyncUiLangRequest(BaseModel):
    telegram_id: int
    ui_language: str


@router.post("/sync-ui-lang", dependencies=[Depends(verify_bot_secret)])
async def sync_ui_lang(
    body: SyncUiLangRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Синхронизирует ui_language из бота в БД API."""
    user = await _get_or_create_user(db, body.telegram_id)

    if body.ui_language not in ("en", "ru", "uk"):
        log.warning("sync-ui-lang: invalid language %s", body.ui_language)
        return {"status": "invalid_lang"}

    user.ui_language = body.ui_language
    await db.flush()
    log.info("sync-ui-lang: updated user=%s lang=%s", user.id, body.ui_language)
    return {"status": "ok"}


# ── Internal: user settings for bot persistence ────────────────────────────────

class UserSettingsRequest(BaseModel):
    telegram_id: int


class UserSettingsResponse(BaseModel):
    target_language: str
    ui_language: str
    favorite_langs: list[str]
    plan: str
    chars_limit: int
    chars_used: int
    chars_remaining: int
    reset_at: Optional[str] = None


class DeductCharsRequest(BaseModel):
    telegram_id: int
    char_count: int


class UpdateSettingsRequest(BaseModel):
    telegram_id: int
    target_language: Optional[str] = None
    ui_language: Optional[str] = None
    favorite_langs: Optional[list[str]] = None


async def _get_or_create_user(db: AsyncSession, telegram_id: int) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=telegram_id,
            telegram_id_hash=hash_telegram_id(telegram_id),
        )
        db.add(user)
        await db.flush()
        log.info("auto-created user telegram_id=%s id=%s", telegram_id, user.id)
    return user


@router.post(
    "/user/settings",
    dependencies=[Depends(verify_bot_secret)],
    response_model=UserSettingsResponse,
)
async def get_user_settings(
    body: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Возвращает настройки пользователя по telegram_id для бота."""
    user = await _get_or_create_user(db, body.telegram_id)

    quota = await get_or_create_quota(db, user.id)

    return UserSettingsResponse(
        target_language=user.target_language or "en",
        ui_language=user.ui_language or "",
        favorite_langs=user.favorite_langs or ["en", "de", "fr"],
        plan=quota.plan,
        chars_limit=quota.chars_limit,
        chars_used=quota.chars_used,
        chars_remaining=quota.chars_remaining,
        reset_at=quota.reset_at.isoformat() if quota.reset_at else None,
    )


@router.post(
    "/user/deduct-chars",
    dependencies=[Depends(verify_bot_secret)],
    response_model=UserSettingsResponse,
)
async def deduct_user_chars(
    body: DeductCharsRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Списывает символы пользователя (вызов из бота после перевода)."""
    user = await _get_or_create_user(db, body.telegram_id)

    from services.quota import deduct_chars as quota_deduct
    quota = await quota_deduct(db, user.id, body.char_count)

    return UserSettingsResponse(
        target_language=user.target_language or "en",
        ui_language=user.ui_language or "",
        favorite_langs=user.favorite_langs or ["en", "de", "fr"],
        plan=quota.plan,
        chars_limit=quota.chars_limit,
        chars_used=quota.chars_used,
        chars_remaining=quota.chars_remaining,
        reset_at=quota.reset_at.isoformat() if quota.reset_at else None,
    )


@router.post(
    "/user/update-settings",
    dependencies=[Depends(verify_bot_secret)],
    response_model=dict,
)
async def update_user_settings(
    body: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Обновляет настройки пользователя из бота."""
    user = await _get_or_create_user(db, body.telegram_id)

    if body.target_language is not None:
        user.target_language = body.target_language
    if body.ui_language is not None:
        if body.ui_language in ("en", "ru", "uk"):
            user.ui_language = body.ui_language
    if body.favorite_langs is not None:
        user.favorite_langs = body.favorite_langs[:10]

    await db.flush()
    return {"status": "ok"}
