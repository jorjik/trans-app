"""
Redis cache service.
Кэш переводов + rate limiting.
Graceful degradation: если Redis недоступен — работаем без кэша.
"""

import hashlib
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from core.config import settings

log = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await _redis.ping()
            log.info("Redis connected")
        except Exception as e:
            log.warning("Redis unavailable: %s — running without cache", e)
            _redis = None
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# ── Translation cache ──────────────────────────────────────────────────────────

def _translate_key(text: str, src: str, tgt: str, engine: str) -> str:
    raw = f"{text}|{src}|{tgt}|{engine}"
    return "translate:cache:" + hashlib.sha256(raw.encode()).hexdigest()


async def get_cached_translation(
    text: str, src: str, tgt: str, engine: str
) -> Optional[dict]:
    r = await get_redis()
    if not r:
        return None
    try:
        key = _translate_key(text, src, tgt, engine)
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        log.warning("Cache get error: %s", e)
        return None


async def set_cached_translation(
    text: str, src: str, tgt: str, engine: str, data: dict
) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _translate_key(text, src, tgt, engine)
        ttl = settings.cache_ttl_long if len(text) > 500 else settings.cache_ttl_short
        await r.setex(key, ttl, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        log.warning("Cache set error: %s", e)


# ── Rate limiting ──────────────────────────────────────────────────────────────

async def check_rate_limit(user_id: int, max_per_minute: int = 30) -> bool:
    """
    Возвращает True если запрос разрешён, False если превышен лимит.
    Sliding window через Redis INCR + EXPIRE.
    """
    r = await get_redis()
    if not r:
        return True  # без Redis — не блокируем

    key = f"ratelimit:user:{user_id}:translate"
    try:
        pipe = r.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, 60)
        results = await pipe.execute()
        count = results[0]
        return count <= max_per_minute
    except Exception as e:
        log.warning("Rate limit check error: %s", e)
        return True  # не блокируем при ошибке


# ── Generic cache ──────────────────────────────────────────────────────────────

async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    if not r:
        return None
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        await r.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception as e:
        log.warning("Cache set error: %s", e)


async def cache_delete(key: str) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        await r.delete(key)
    except Exception:
        pass
