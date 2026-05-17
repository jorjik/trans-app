"""CRUD /chats — управление авто-переводами чатов."""

import logging

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError, ForbiddenError, AppError
from db.session import get_db
from models import ChatConfig, User
from schemas import (
    ChatConfigCreate, ChatConfigUpdate,
    ChatConfigResponse, ChatListResponse,
)
from services.auth import get_current_user
from services.quota import get_or_create_quota, get_max_chats

log = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatListResponse:
    """Список авто-переводов пользователя."""
    quota = await get_or_create_quota(db, current_user.id)
    max_chats = get_max_chats(quota.plan)

    result = await db.execute(
        select(ChatConfig)
        .where(ChatConfig.user_id == current_user.id)
        .order_by(ChatConfig.created_at.desc())
    )
    configs = result.scalars().all()

    return ChatListResponse(
        items=[ChatConfigResponse.model_validate(c) for c in configs],
        total=len(configs),
        limit_reached=len(configs) >= max_chats,
        max_chats=max_chats,
    )


@router.post("", response_model=ChatConfigResponse, status_code=201)
async def create_chat(
    body: ChatConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatConfigResponse:
    """Добавить чат для авто-перевода."""
    quota = await get_or_create_quota(db, current_user.id)
    max_chats = get_max_chats(quota.plan)

    # Считаем активные конфиги
    count_res = await db.execute(
        select(func.count()).where(ChatConfig.user_id == current_user.id)
    )
    current_count = count_res.scalar_one()

    if current_count >= max_chats:
        raise AppError(
            status_code=403,
            error="chat_limit_reached",
            message=f"Max {max_chats} auto-translate chats on your plan",
            max_chats=max_chats,
            current_plan=quota.plan,
        )

    if not body.chat_username and not body.chat_id:
        raise AppError(
            status_code=422,
            error="validation_error",
            message="Provide chat_username or chat_id",
        )

    config = ChatConfig(
        user_id=current_user.id,
        chat_id=body.chat_id,
        chat_username=body.chat_username,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
        is_active=True,
    )
    db.add(config)
    await db.flush()

    log.info("Chat config created: user=%s chat=%s", current_user.id, body.chat_username)
    return ChatConfigResponse.model_validate(config)


@router.patch("/{config_id}", response_model=ChatConfigResponse)
async def update_chat(
    config_id: int = Path(...),
    body: ChatConfigUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatConfigResponse:
    """Обновить настройки авто-перевода."""
    config = await _get_user_config(db, config_id, current_user.id)

    if body.source_lang is not None:
        config.source_lang = body.source_lang
    if body.target_lang is not None:
        config.target_lang = body.target_lang
    if body.is_active is not None:
        config.is_active = body.is_active

    db.add(config)
    return ChatConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=204)
async def delete_chat(
    config_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить авто-перевод."""
    config = await _get_user_config(db, config_id, current_user.id)
    await db.delete(config)


async def _get_user_config(
    db: AsyncSession,
    config_id: int,
    user_id: int,
) -> ChatConfig:
    result = await db.execute(
        select(ChatConfig).where(ChatConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("Chat config")
    if config.user_id != user_id:
        raise ForbiddenError("Not your config")
    return config
