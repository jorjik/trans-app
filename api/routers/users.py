"""GET /users/me, PATCH /users/me."""

from fastapi import APIRouter
from sqlalchemy import select

from dependencies import CurrentUser, DB
from schemas import UserResponse, UserUpdateRequest
from services.quota import get_or_create_quota

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser, db: DB) -> UserResponse:
    quota = await get_or_create_quota(db, user.id)
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


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    user: CurrentUser,
    db: DB,
) -> UserResponse:
    if body.target_language is not None:
        user.target_language = body.target_language
        langs = user.favorite_langs or []
        if body.target_language not in langs:
            langs.insert(0, body.target_language)
            user.favorite_langs = langs[:5]

    if body.favorite_langs is not None:
        user.favorite_langs = body.favorite_langs[:10]

    if body.preferred_engine is not None:
        user.preferred_engine = body.preferred_engine

    await db.flush()
    quota = await get_or_create_quota(db, user.id)

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