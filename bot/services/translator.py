"""
Translation Service — абстракция над MT-провайдерами.
MVP: использует deep-translator (Google бесплатно, без API ключа).
Кэш: Redis (если настроен), fallback на in-memory с TTL.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    TranslationNotFound,
    LanguageNotSupportedException,
)

from config import settings
from utils.languages import detect_language, to_google_lang
from services.cache import get_redis_cache

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    cached: bool = False
    char_count: int = 0

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.original_text)


# In-memory fallback cache (используется когда Redis недоступен)
_memory_cache: dict[str, tuple[float, TranslationResult]] = {}
MAX_MEMORY_CACHE = settings.max_translation_cache
CACHE_TTL = settings.translation_cache_ttl


def _cache_key(text: str, src: str, tgt: str) -> str:
    raw = f"{text}|{src}|{tgt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _get_from_cache(key: str) -> Optional[TranslationResult]:
    """Пытается прочитать из Redis, затем из in-memory."""
    # Redis
    redis = await get_redis_cache()
    if redis:
        try:
            import json
            data = await redis.get(f"tr:{key}")
            if data:
                raw = json.loads(data)
                result = TranslationResult(
                    original_text=raw["original_text"],
                    translated_text=raw["translated_text"],
                    source_lang=raw["source_lang"],
                    target_lang=raw["target_lang"],
                    provider=raw["provider"],
                    cached=True,
                    char_count=raw.get("char_count", 0),
                )
                return result
        except Exception as e:
            logger.debug("Redis cache read error: %s", e)

    # In-memory fallback
    entry = _memory_cache.get(key)
    if entry:
        ts, result = entry
        if datetime.now(timezone.utc).timestamp() - ts < CACHE_TTL:
            result.cached = True
            return result
        del _memory_cache[key]

    return None


async def _put_to_cache(key: str, result: TranslationResult) -> None:
    """Сохраняет в Redis (если доступен) и в in-memory."""
    # In-memory
    if len(_memory_cache) >= MAX_MEMORY_CACHE:
        oldest = next(iter(_memory_cache))
        del _memory_cache[oldest]
    _memory_cache[key] = (datetime.now(timezone.utc).timestamp(), result)

    # Redis (fire-and-forget)
    redis = await get_redis_cache()
    if redis:
        try:
            import json
            data = json.dumps({
                "original_text": result.original_text,
                "translated_text": result.translated_text,
                "source_lang": result.source_lang,
                "target_lang": result.target_lang,
                "provider": result.provider,
                "char_count": result.char_count,
            })
            await redis.setex(f"tr:{key}", CACHE_TTL, data)
        except Exception as e:
            logger.debug("Redis cache write error: %s", e)


async def translate(
    text: str,
    target_lang: str,
    source_lang: str = "auto",
) -> TranslationResult:
    """
    Переводит текст. Использует кэш, затем Google Translate.

    Args:
        text: исходный текст
        target_lang: ISO код языка назначения (например 'ru', 'en')
        source_lang: ISO код языка источника или 'auto'

    Returns:
        TranslationResult

    Raises:
        ValueError: если язык не поддерживается
        RuntimeError: если перевод не удался
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty text")

    if len(text) > 10_000:
        return await _translate_long(text, target_lang, source_lang)

    # Определяем язык источника
    detected_lang = source_lang
    if source_lang == "auto":
        detected_lang = detect_language(text) or "auto"

    # Проверяем кэш
    key = _cache_key(text, detected_lang, target_lang)
    cached = await _get_from_cache(key)
    if cached:
        logger.debug("Cache hit for key %s", key[:8])
        return cached

    # Делаем перевод в отдельном потоке (deep-translator — синхронный)
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        _do_translate_sync,
        text,
        target_lang,
        source_lang,
        detected_lang,
    )

    await _put_to_cache(key, result)
    return result


def _do_translate_sync(
    text: str,
    target_lang: str,
    source_lang: str,
    detected_lang: str,
) -> TranslationResult:
    """Синхронный вызов Google Translate через deep-translator."""
    try:
        src = "auto" if source_lang == "auto" else to_google_lang(source_lang)
        tgt = to_google_lang(target_lang)
        translator = GoogleTranslator(source=src, target=tgt)
        translated = translator.translate(text)

        if not translated:
            raise RuntimeError("Empty translation result")

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_lang=detected_lang,
            target_lang=target_lang,
            provider="google_free",
            char_count=len(text),
        )

    except LanguageNotSupportedException as e:
        raise ValueError(f"Language not supported: {e}") from e
    except TranslationNotFound as e:
        raise RuntimeError(f"Translation not found: {e}") from e
    except Exception as e:
        logger.error("Translation error: %s", e)
        raise RuntimeError(f"Translation failed: {e}") from e


async def _translate_long(
    text: str,
    target_lang: str,
    source_lang: str,
) -> TranslationResult:
    """Переводит длинный текст по чанкам. Кэширует полный результат."""
    chunk_size = settings.translate_chunk_size

    # Проверяем кэш для полного текста
    detected_lang = source_lang
    if source_lang == "auto":
        detected_lang = detect_language(text) or "auto"

    full_key = _cache_key(text, detected_lang, target_lang)
    full_cached = await _get_from_cache(full_key)
    if full_cached:
        logger.debug("Long text cache hit for key %s", full_key[:8])
        return full_cached

    # Переводим по чанкам
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    translated_parts = []
    last_source_lang = detected_lang

    for chunk in chunks:
        result = await translate(chunk, target_lang, source_lang if source_lang != "auto" else last_source_lang)
        translated_parts.append(result.translated_text)
        last_source_lang = result.source_lang  # используем определённый язык для следующих чанков

    full_result = TranslationResult(
        original_text=text,
        translated_text="\n".join(translated_parts),
        source_lang=last_source_lang,
        target_lang=target_lang,
        provider="google_free",
        char_count=len(text),
    )

    # Кэшируем полный результат
    await _put_to_cache(full_key, full_result)
    return full_result


async def get_cache_stats() -> dict:
    """Возвращает статистику кэша."""
    redis = await get_redis_cache()
    redis_keys = 0
    if redis:
        try:
            redis_keys = await redis.dbsize() or 0
        except Exception:
            pass

    return {
        "memory_size": len(_memory_cache),
        "memory_max": MAX_MEMORY_CACHE,
        "redis_available": redis is not None,
        "redis_keys_approx": redis_keys,
    }
