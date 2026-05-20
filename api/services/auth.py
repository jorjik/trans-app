"""
Auth service — FastAPI dependency для получения текущего пользователя.
Создаёт пользователя в БД при первом визите.
"""

import logging
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import UnauthorizedError
from core.security import decode_access_token, hash_telegram_id, validate_init_data, InitDataError
from db.session import get_db
from models import User, Quota
from services.quota import get_or_create_quota
from core.config import settings

log = logging.getLogger(__name__)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency. Декодирует JWT из заголовка Authorization.
    Возвращает объект User из БД.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise UnauthorizedError(str(e))

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def get_or_create_user(
    telegram_user: dict,
    db: AsyncSession,
) -> User:
    """
    Находит или создаёт пользователя по telegram_id.
    Вызывается при авторизации через initData.
    """
    telegram_id = int(telegram_user["id"])
    id_hash = hash_telegram_id(telegram_id)

    # Пробуем найти по хэшу
    result = await db.execute(
        select(User).where(User.telegram_id_hash == id_hash)
    )
    user = result.scalar_one_or_none()

    if user:
        # Обновляем имя/username если изменились
        user.first_name = telegram_user.get("first_name")
        user.username = telegram_user.get("username")
        user.language_code = telegram_user.get("language_code", user.language_code)
        await db.flush()
        return user, False

    # Создаём нового пользователя
    lang_code = telegram_user.get("language_code", "en")[:2]
    target_lang = lang_code if lang_code in ("en", "ru", "uk") else "en"

    user = User(
        telegram_id=telegram_id,
        telegram_id_hash=id_hash,
        username=telegram_user.get("username"),
        first_name=telegram_user.get("first_name"),
        language_code=telegram_user.get("language_code", "en"),
        ui_language=lang_code if lang_code in ("en", "ru", "uk") else "en",
        target_language=target_lang,
        favorite_langs=_default_langs(target_lang),
    )
    db.add(user)
    await db.flush()  # получаем user.id

    # Создаём квоту
    await get_or_create_quota(db, user.id)

    log.info("New user created: id=%s", user.id)
    return user, True


def _default_langs(primary: str) -> list[str]:
    """Дефолтные любимые языки в зависимости от основного языка пользователя."""
    defaults = {
        "ru": ["en", "de", "fr", "uk", "tr"],
        "uk": ["ru", "en", "de", "pl", "fr"],
        "en": ["es", "fr", "de", "it", "pt"],
        "de": ["en", "fr", "es", "it", "pl"],
        "fr": ["en", "es", "de", "it", "pt"],
        "es": ["en", "fr", "pt", "de", "it"],
        "zh": ["en", "ja", "ko", "de", "fr"],
        "ja": ["en", "zh", "ko", "de", "fr"],
        "ar": ["en", "fr", "de", "tr", "es"],
        "tr": ["en", "de", "ru", "ar", "fr"],
    }
    langs = defaults.get(primary, ["en", "de", "fr", "es", "it"])
    # Основной язык не дублируем в любимых
    return [l for l in langs if l != primary][:5]


# Удобный тип для инжекции в роутеры
CurrentUser = Annotated[User, Depends(get_current_user)]
