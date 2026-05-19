"""POST /auth/telegram — авторизация через Telegram initData."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import validate_init_data, create_access_token, InitDataError
from core.errors import UnauthorizedError
from core.config import settings
from db.session import get_db
from schemas import TelegramAuthRequest, TokenResponse, UserResponse
from services.auth import get_or_create_user
from services.quota import get_or_create_quota

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(
    body: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Валидирует Telegram initData (HMAC) и возвращает JWT.
    Создаёт пользователя при первом визите.
    """
    try:
        tg_user = validate_init_data(body.init_data)
    except InitDataError as e:
        raise UnauthorizedError(f"Invalid init_data: {e}")

    user = await get_or_create_user(tg_user, db)
    quota = await get_or_create_quota(db, user.id)

    token = create_access_token(user.id, user.telegram_id)

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_seconds,
        user=UserResponse(
            id=user.id,
            ui_language=user.ui_language,
            target_language=user.target_language,
            favorite_langs=user.favorite_langs or [],
            preferred_engine=user.preferred_engine,
            plan=quota.plan,
            chars_limit=quota.chars_limit,
            chars_used=quota.chars_used,
            chars_remaining=quota.chars_remaining,
            reset_at=quota.reset_at,
            created_at=user.created_at,
        ),
    )
