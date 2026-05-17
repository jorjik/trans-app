"""GET /users/me, PATCH /users/me — настройки пользователя."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models import User
from schemas import UserResponse, UserUpdateRequest
from services.auth import get_current_user
from services.quota import get_or_create_quota

router = APIRouter(prefix="/users", tags=["users"])


def _build_user_response(user: User, quota) -> UserResponse:
    return UserResponse(
        id=user.id,
        target_language=user.target_language,
        favorite_langs=user.favorite_langs or [],
        preferred_engine=user.preferred_engine,
        plan=quota.plan,
        chars_limit=quota.chars_limit,
        chars_used=quota.chars_used,
        chars_remaining=quota.chars_remaining,
        reset_at=quota.reset_at,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Возвращает профиль и баланс текущего пользователя."""
    quota = await get_or_create_quota(db, current_user.id)
    return _build_user_response(current_user, quota)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Обновляет настройки: язык, любимые языки, движок перевода."""
    if body.target_language is not None:
        current_user.target_language = body.target_language
        # Добавляем в начало избранных если ещё нет
        favs = current_user.favorite_langs or []
        if body.target_language not in favs:
            favs = [body.target_language] + favs
        current_user.favorite_langs = favs[:10]

    if body.favorite_langs is not None:
        current_user.favorite_langs = body.favorite_langs[:10]

    if body.preferred_engine is not None:
        current_user.preferred_engine = body.preferred_engine

    db.add(current_user)
    quota = await get_or_create_quota(db, current_user.id)
    return _build_user_response(current_user, quota)
