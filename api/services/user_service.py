"""Р Р°Р±РѕС‚Р° СЃ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРјРё РІ Р‘Р”."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Quota
from core.security import hash_telegram_id
from services.quota import get_or_create_quota
from services.constants import PLAN_LIMITS

logger = logging.getLogger(__name__)


async def get_user_by_hash(db: AsyncSession, tg_hash: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.telegram_id_hash == tg_hash))
    return result.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    language_code: str = "en",
) -> tuple[User, bool]:
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ (user, created). created=True РµСЃР»Рё РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃРѕР·РґР°РЅ."""
    tg_hash = hash_telegram_id(telegram_id)
    user = await get_user_by_hash(db, tg_hash)

    if user:
        # РћР±РЅРѕРІР»СЏРµРј РґР°РЅРЅС‹Рµ РµСЃР»Рё РёР·РјРµРЅРёР»РёСЃСЊ
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if changed:
            await db.flush()
        return user, False

    # РЎРѕР·РґР°С‘Рј РЅРѕРІРѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
    ui_lang = language_code if language_code in ("en", "ru", "uk") else "en"
    user = User(
        telegram_id=telegram_id,
        telegram_id_hash=tg_hash,
        username=username,
        first_name=first_name,
        language_code=language_code,
        ui_language=ui_lang,
        target_language=language_code if language_code in ("ru", "en", "de", "fr", "es", "uk") else "en",
        favorite_langs=["en", "ru", "de"],
        preferred_engine="auto",
    )
    db.add(user)
    await db.flush()

    # РЎРѕР·РґР°С‘Рј РєРІРѕС‚Сѓ
    await get_or_create_quota(db, user.id)

    logger.info("New user registered: id=%d, lang=%s", user.id, language_code)
    return user, True


async def get_user_with_quota(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await get_or_create_quota(db, user.id)
    return user