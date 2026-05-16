"""
Redis-based кэш и rate limiting.
Graceful degradation: если Redis недоступен — продолжаем без кэша.
"""

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from core.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is None:
        try:
            _redis = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await _redis.ping()
        except Exception as e:
            logger.warning("Redis unavailable: %s — running without cache", e)
            _redis = None
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# ── Translation cache ──────────────────────────────────────────────────────────

def _translation_key(text: str, src: str, tgt: str, engine: str) -> str:
    raw = f"{text}|{src}|{tgt}|{engine}"
    return "translate:cache:" + hashlib.sha256(raw.encode()).hexdigest()


async def get_cached_translation(
    text: str, src: str, tgt: str, engine: str
) -> Optional[dict]:
    r = await get_redis()
    if not r:
        return None
    try:
        key = _translation_key(text, src, tgt, engine)
        value = await r.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning("Cache get error: %s", e)
    return None


async def set_cached_translation(
    text: str, src: str, tgt: str, engine: str, data: dict
) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _translation_key(text, src, tgt, engine)
        ttl = settings.cache_ttl_long if len(text) > 500 else settings.cache_ttl_short
        await r.setex(key, ttl, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        logger.warning("Cache set error: %s", e)


# ── Rate limiting ──────────────────────────────────────────────────────────────

async def check_rate_limit(user_id: int, limit: int = 10, window: int = 60) -> bool:
    """
    Sliding window rate limit.
    Возвращает True если запрос разрешён, False если превышен лимит.
    """
    r = await get_redis()
    if not r:
        return True  # без Redis не ограничиваем

    key = f"ratelimit:user:{user_id}:translate"
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        count = results[0]
        return count <= limit
    except Exception as e:
        logger.warning("Rate limit check error: %s", e)
        return True


# ── Session store (Mini App JWT) ───────────────────────────────────────────────

async def store_session(token: str, data: dict, ttl: int = 3600) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        await r.setex(
            f"session:miniapp:{token}",
            ttl,
            json.dumps(data),
        )
    except Exception as e:
        logger.warning("Session store error: %s", e)


async def get_session(token: str) -> Optional[dict]:
    r = await get_redis()
    if not r:
        return None
    try:
        value = await r.get(f"session:miniapp:{token}")
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning("Session get error: %s", e)
        return None
