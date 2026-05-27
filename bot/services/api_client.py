"""
API client — общение бота с Backend API.
Все пользовательские данные хранятся в БД API, бот их кэширует с TTL.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

import aiohttp

from config import settings

log = logging.getLogger(__name__)


@dataclass
class UserData:
    telegram_id: int
    target_language: str = "en"
    ui_language: str = ""
    favorite_langs: list[str] = field(default_factory=lambda: ["en", "de", "fr"])
    plan: str = "free"
    chars_limit: int = 25_000
    chars_used: int = 0
    chars_remaining: int = 25_000
    reset_at: Optional[str] = None

    @property
    def is_quota_exceeded(self) -> bool:
        return self.chars_used >= self.chars_limit

    def to_settings_dict(self) -> dict:
        return asdict(self)


# ── In-memory cache with TTL ──────────────────────────────────────────────────

_cache: dict[int, tuple[float, UserData]] = {}
CACHE_TTL = 60  # seconds


def _cache_get(tg_id: int) -> Optional[UserData]:
    entry = _cache.get(tg_id)
    if entry:
        ts, data = entry
        if datetime.now(timezone.utc).timestamp() - ts < CACHE_TTL:
            return data
        del _cache[tg_id]
    return None


def _cache_set(tg_id: int, data: UserData) -> None:
    _cache[tg_id] = (datetime.now(timezone.utc).timestamp(), data)


def _cache_invalidate(tg_id: int) -> None:
    _cache.pop(tg_id, None)


# ── HTTP helpers ──────────────────────────────────────────────────────────────

_headers: dict[str, str] = {}
_session: Optional[aiohttp.ClientSession] = None


def _ensure_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


def _api_url(path: str) -> str:
    base = settings.api_url or ""
    return f"{base.rstrip('/')}{path}"


def _bot_secret_headers() -> dict[str, str]:
    return {"X-Bot-Secret": settings.bot_internal_secret or ""}


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
    _session = None


# ── Public API ────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> UserData:
    """
    Получает данные пользователя из API.
    Использует in-memory кэш с TTL=60с.
    При недоступности API возвращает кэшированные/дефолтные данные.
    """
    # Проверяем кэш
    cached = _cache_get(telegram_id)
    if cached:
        return cached

    # Если API не настроен, возвращаем дефолт
    if not settings.api_url:
        user = UserData(telegram_id=telegram_id)
        _cache_set(telegram_id, user)
        return user

    # Запрашиваем из API через внутренний эндпоинт
    try:
        session = _ensure_session()
        url = _api_url("/internal/user/settings")
        async with session.post(
            url,
            json={"telegram_id": telegram_id},
            headers=_bot_secret_headers(),
            timeout=10,
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                user = UserData(
                    telegram_id=telegram_id,
                    target_language=data.get("target_language", "en"),
                    ui_language=data.get("ui_language", ""),
                    favorite_langs=data.get("favorite_langs", ["en", "de", "fr"]),
                    plan=data.get("plan", "free"),
chars_limit=data.get("chars_limit", 25_000),
                    chars_used=data.get("chars_used", 0),
                    chars_remaining=data.get("chars_remaining", 25_000),
                 )
                _cache_set(telegram_id, user)
                return user
            elif resp.status == 404:
                # Пользователь не найден в API — создадим локально
                user = UserData(telegram_id=telegram_id)
                _cache_set(telegram_id, user)
                return user
            else:
                log.warning("API get_user failed status=%s", resp.status)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("API get_user error: %s", e)

    # Fallback: возвращаем кэш (даже просроченный) или дефолт
    if telegram_id in _cache:
        return _cache[telegram_id][1]
    user = UserData(telegram_id=telegram_id)
    _cache_set(telegram_id, user)
    return user


async def deduct_chars(telegram_id: int, count: int) -> Optional[UserData]:
    """Списывает символы через API. При ошибке — инвалидация кэша."""
    if not settings.api_url:
        return None

    try:
        session = _ensure_session()
        url = _api_url("/internal/user/deduct-chars")
        async with session.post(
            url,
            json={"telegram_id": telegram_id, "char_count": count},
            headers=_bot_secret_headers(),
            timeout=10,
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                user = UserData(
                    telegram_id=telegram_id,
                    target_language=data.get("target_language", "en"),
                    ui_language=data.get("ui_language", ""),
                    favorite_langs=data.get("favorite_langs", ["en", "de", "fr"]),
                    plan=data.get("plan", "free"),
                    chars_limit=data.get("chars_limit", 25_000),
                    chars_used=data.get("chars_used", 0),
                    chars_remaining=data.get("chars_remaining", 25_000),
                    reset_at=data.get("reset_at"),
                )
                _cache_set(telegram_id, user)
                return user
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("API deduct_chars error: %s", e)

    # Fallback: инвалидируем кэш, при след. запросе перечитаем
    _cache_invalidate(telegram_id)
    return None


async def update_settings(
    telegram_id: int,
    *,
    target_language: Optional[str] = None,
    ui_language: Optional[str] = None,
    favorite_langs: Optional[list[str]] = None,
) -> bool:
    """Обновляет настройки пользователя через API."""
    if not settings.api_url:
        return False

    body: dict[str, Any] = {"telegram_id": telegram_id}
    if target_language is not None:
        body["target_language"] = target_language
    if ui_language is not None:
        body["ui_language"] = ui_language
    if favorite_langs is not None:
        body["favorite_langs"] = favorite_langs

    try:
        session = _ensure_session()
        url = _api_url("/internal/user/update-settings")
        async with session.post(
            url,
            json=body,
            headers=_bot_secret_headers(),
            timeout=10,
        ) as resp:
            if resp.status == 200:
                _cache_invalidate(telegram_id)
                return True
            log.warning("API update_settings failed status=%s", resp.status)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("API update_settings error: %s", e)

    return False


async def upgrade_plan(telegram_id: int, plan: str) -> bool:
    """Апгрейд тарифа через API. Возвращает True при успехе."""
    if not settings.api_url:
        return False

    try:
        session = _ensure_session()
        url = _api_url("/billing/internal/stars")
        headers = {"X-Billing-Secret": settings.bot_webhook_secret or ""}
        async with session.post(
            url,
            json={
                "telegram_id": telegram_id,
                "plan_id": plan,
                "telegram_payment_charge_id": f"bot_upgrade_{telegram_id}_{plan}",
                "total_amount": 0,
            },
            headers=headers,
            timeout=15,
        ) as resp:
            if resp.status == 200:
                _cache_invalidate(telegram_id)
                return True
            log.warning("API upgrade_plan failed status=%s", resp.status)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("API upgrade_plan error: %s", e)

    return False
