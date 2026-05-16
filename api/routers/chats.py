"""CRUD /chats вЂ” СѓРїСЂР°РІР»РµРЅРёРµ Р°РІС‚Рѕ-РїРµСЂРµРІРѕРґР°РјРё."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from dependencies import CurrentUser, DB
from models import ChatConfig
from schemas import (
    ChatConfigCreate, ChatConfigUpdate,
    ChatConfigResponse, ChatListResponse,
)
from services.quota import get_max_chats, get_or_create_quota

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats(user: CurrentUser, db: DB) -> ChatListResponse:
    quota = await get_or_create_quota(db, user.id)
    max_chats = get_max_chats(quota.plan)

    result = await db.execute(
        select(ChatConfig)
        .where(ChatConfig.user_id == user.id)
        .order_by(ChatConfig.created_at.desc())
    )
    chats = result.scalars().all()

    return ChatListResponse(
        items=[ChatConfigResponse.model_validate(c) for c in chats],
        total=len(chats),
        limit_reached=len(chats) >= max_chats,
        max_chats=max_chats,
    )


@router.post("", response_model=ChatConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(body: ChatConfigCreate, user: CurrentUser, db: DB) -> ChatConfigResponse:
    quota = await get_or_create_quota(db, user.id)
    max_chats = get_max_chats(quota.plan)

    count_result = await db.execute(
        select(func.count()).select_from(ChatConfig).where(ChatConfig.user_id == user.id)
    )
    count = count_result.scalar()
    if count >= max_chats:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Chat limit reached ({max_chats}). Upgrade your plan.",
        )

    chat = ChatConfig(
        user_id=user.id,
        chat_id=body.chat_id or 0,
        chat_username=body.chat_username,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
        is_active=True,
    )
    db.add(chat)
    await db.flush()
    return ChatConfigResponse.model_validate(chat)


@router.patch("/{chat_id}", response_model=ChatConfigResponse)
async def update_chat(chat_id: int, body: ChatConfigUpdate, user: CurrentUser, db: DB) -> ChatConfigResponse:
    result = await db.execute(
        select(ChatConfig).where(ChatConfig.id == chat_id, ChatConfig.user_id == user.id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if body.source_lang is not None:
        chat.source_lang = body.source_lang
    if body.target_lang is not None:
        chat.target_lang = body.target_lang
    if body.is_active is not None:
        chat.is_active = body.is_active

    await db.flush()
    return ChatConfigResponse.model_validate(chat)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: int, user: CurrentUser, db: DB) -> None:
    result = await db.execute(
        select(ChatConfig).where(ChatConfig.id == chat_id, ChatConfig.user_id == user.id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.delete(chat)