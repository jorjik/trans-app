"""POST /auth/telegram вЂ” РІР°Р»РёРґР°С†РёСЏ Telegram initData Рё РІС‹РґР°С‡Р° JWT."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import validate_init_data, InitDataError, create_access_token
from db.session import get_db
from schemas import TelegramAuthRequest, AuthResponse, UserBrief
from services.user_service import get_or_create_user
from services.quota import get_or_create_quota
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(
    body: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    РђРІС‚РѕСЂРёР·Р°С†РёСЏ С‡РµСЂРµР· Telegram WebApp initData.
    РЎРѕР·РґР°С‘С‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РїСЂРё РїРµСЂРІРѕРј РІС…РѕРґРµ.
    """
    try:
        tg_user = validate_init_data(body.init_data)
    except InitDataError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    telegram_id = tg_user["id"]
    user, created = await get_or_create_user(
        db,
        telegram_id=telegram_id,
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        language_code=tg_user.get("language_code", "en"),
    )

    if created:
        logger.info("New user via Mini App: tg_id=%d", telegram_id)

    quota = await get_or_create_quota(db, user.id)
    token = create_access_token(user.id, telegram_id)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_seconds,
        user=UserBrief(
            id=user.id,
            telegram_id_hash=user.telegram_id_hash,
            target_language=user.target_language,
            plan=quota.plan,
            chars_remaining=quota.chars_remaining,
        ),
    )