"""Internal API — endpoints для взаимодействия бота с API (защищены общим секретом)."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core.config import settings
from db.session import get_db
from models import User

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
    result = await db.execute(
        select(User).where(User.telegram_id == body.telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        log.warning("sync-ui-lang: user not found telegram_id=%s", body.telegram_id)
        return {"status": "not_found"}

    if body.ui_language not in ("en", "ru", "uk"):
        log.warning("sync-ui-lang: invalid language %s", body.ui_language)
        return {"status": "invalid_lang"}

    user.ui_language = body.ui_language
    db.add(user)
    await db.flush()
    log.info("sync-ui-lang: updated user=%s lang=%s", user.id, body.ui_language)
    return {"status": "ok"}
