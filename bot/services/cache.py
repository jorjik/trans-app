"""
Redis cache helper for bot services.
Provides a shared redis connection and helper functions.
"""

from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from config import settings

log = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Возвращает Redis-клиент (создаёт при первом вызове)."""
    global _redis
    if _redis is None:
        if not settings.use_redis:
            log.debug("Redis disabled by config")
            return None
        try:
            _redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            await _redis.ping()
            log.info("Redis connected")
        except Exception as e:
            log.warning("Redis unavailable: %s — running without cache", e)
            _redis = None
    return _redis


async def close_redis() -> None:
    """Закрывает Redis-соединение."""
    global _redis
    if _redis:
        try:
            await _redis.close()
        except Exception as e:
            log.debug("Redis close error: %s", e)
        _redis = None


async def get_redis_cache() -> Optional[aioredis.Redis]:
    """Удобная обёртка — возвращает Redis или None."""
    try:
        return await get_redis()
    except Exception:
        return None
