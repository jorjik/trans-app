"""
Translation Service — абстракция над MT-провайдерами.
MVP: использует deep-translator (Google бесплатно, без API ключа).
Легко заменить на DeepL / OpenAI.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Optional

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    TranslationNotFound,
    LanguageNotSupportedException,
)

from config import settings
from utils.languages import detect_language

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


# In-memory кэш (пока нет Redis)
_memory_cache: dict[str, TranslationResult] = {}
MAX_MEMORY_CACHE = 500  # ограничение


def _cache_key(text: str, src: str, tgt: str) -> str:
    raw = f"{text}|{src}|{tgt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _get_from_cache(key: str) -> Optional[TranslationResult]:
    return _memory_cache.get(key)


def _put_to_cache(key: str, result: TranslationResult) -> None:
    if len(_memory_cache) >= MAX_MEMORY_CACHE:
        # Удаляем старейший элемент
        oldest = next(iter(_memory_cache))
        del _memory_cache[oldest]
    _memory_cache[key] = result


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
        # Разбиваем на части и переводим
        return await _translate_long(text, target_lang, source_lang)

    # Определяем язык источника
    detected_lang = source_lang
    if source_lang == "auto":
        detected_lang = detect_language(text) or "auto"

    # Проверяем кэш
    key = _cache_key(text, detected_lang, target_lang)
    cached = _get_from_cache(key)
    if cached:
        logger.debug("Cache hit for key %s", key[:8])
        cached.cached = True
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

    _put_to_cache(key, result)
    return result


def _do_translate_sync(
    text: str,
    target_lang: str,
    source_lang: str,
    detected_lang: str,
) -> TranslationResult:
    """Синхронный вызов Google Translate через deep-translator."""
    try:
        src = "auto" if source_lang == "auto" else source_lang
        translator = GoogleTranslator(source=src, target=target_lang)
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
    chunk_size: int = 4500,
) -> TranslationResult:
    """Переводит длинный текст по чанкам."""
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    translated_parts = []

    for chunk in chunks:
        result = await translate(chunk, target_lang, source_lang)
        translated_parts.append(result.translated_text)
        source_lang = result.source_lang  # используем определённый язык для следующих чанков

    return TranslationResult(
        original_text=text,
        translated_text="\n".join(translated_parts),
        source_lang=result.source_lang,
        target_lang=target_lang,
        provider="google_free",
        char_count=len(text),
    )


def get_cache_stats() -> dict:
    return {"size": len(_memory_cache), "max": MAX_MEMORY_CACHE}
