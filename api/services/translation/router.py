"""
Translation Router — выбор провайдера, кэш, fallback, подсчёт символов.

Логика:
  1. Проверить кэш Redis
  2. Выбрать провайдера (по настройке или auto)
  3. Попробовать перевод; при ошибке — fallback на следующий
  4. Сохранить в кэш
"""

import logging
import time
from typing import Optional

from core.config import settings
from services.translation.base import BaseTranslationProvider, TranslationResult
from services.translation.google import GoogleFreeProvider
from services.cache import get_cached_translation, set_cached_translation

log = logging.getLogger(__name__)

# Singleton провайдеры
_google_free = GoogleFreeProvider()
_deepl: Optional[BaseTranslationProvider] = None
_providers_initialized = False


def _init_providers() -> None:
    global _deepl, _providers_initialized
    if _providers_initialized:
        return

    if settings.deepl_api_key:
        try:
            from services.translation.deepl import DeepLProvider
            _deepl = DeepLProvider()
            log.info("DeepL provider initialized")
        except Exception as e:
            log.warning("DeepL init failed: %s", e)

    _providers_initialized = True


def _pick_provider(engine: str, target_lang: str) -> list[BaseTranslationProvider]:
    """
    Возвращает список провайдеров в порядке приоритета.
    Первый — основной, остальные — fallback.
    """
    _init_providers()

    if engine == "deepl" and _deepl:
        return [_deepl, _google_free]

    if engine == "google" or engine == "google_free":
        return [_google_free]

    # auto: DeepL если есть и поддерживает язык, иначе Google
    if engine == "auto":
        if _deepl and _deepl.supports_language(target_lang):
            return [_deepl, _google_free]
        return [_google_free]

    return [_google_free]


async def translate(
    text: str,
    target_lang: str,
    source_lang: str = "auto",
    engine: str = "auto",
) -> TranslationResult:
    """
    Главная функция перевода. Использует кэш и fallback.

    Args:
        text:        исходный текст (max 10_000 символов)
        target_lang: ISO код языка назначения
        source_lang: ISO код или 'auto'
        engine:      'auto' | 'google_free' | 'deepl' | 'openai'

    Returns:
        TranslationResult

    Raises:
        RuntimeError: если все провайдеры недоступны
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty text")

    # Для длинных текстов — разбиваем на чанки
    if len(text) > 4_500:
        return await _translate_chunked(text, target_lang, source_lang, engine)

    # Проверяем кэш
    cached = await get_cached_translation(text, source_lang, target_lang, engine)
    if cached:
        log.debug("Cache hit")
        return TranslationResult(
            original_text=text,
            translated_text=cached["translated_text"],
            source_lang=cached["source_lang"],
            target_lang=target_lang,
            provider=cached["provider"],
            cached=True,
            char_count=len(text),
        )

    # Выбираем провайдеров
    providers = _pick_provider(engine, target_lang)
    last_error: Optional[Exception] = None

    for provider in providers:
        try:
            t0 = time.monotonic()
            result = await provider.translate(text, target_lang, source_lang)
            latency_ms = int((time.monotonic() - t0) * 1000)

            log.info(
                "Translated",
                provider=provider.name,
                chars=result.char_count,
                latency_ms=latency_ms,
                src=result.source_lang,
                tgt=target_lang,
            )

            # Сохраняем в кэш
            await set_cached_translation(
                text, source_lang, target_lang, engine,
                {
                    "translated_text": result.translated_text,
                    "source_lang": result.source_lang,
                    "provider": result.provider,
                },
            )

            return result

        except Exception as e:
            log.warning(
                "Provider %s failed: %s — trying fallback", provider.name, e
            )
            last_error = e
            continue

    raise RuntimeError(
        f"All translation providers failed. Last error: {last_error}"
    )


async def _translate_chunked(
    text: str,
    target_lang: str,
    source_lang: str,
    engine: str,
    chunk_size: int = 4_500,
) -> TranslationResult:
    """Переводит длинный текст по чанкам, склеивает результат."""
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break
        # Разбиваем по абзацу, потом по строке, потом по слову
        for sep in ("\n\n", "\n", " "):
            idx = text.rfind(sep, 0, chunk_size)
            if idx != -1:
                chunks.append(text[:idx])
                text = text[idx + len(sep):]
                break
        else:
            chunks.append(text[:chunk_size])
            text = text[chunk_size:]

    translated_parts = []
    detected_lang = source_lang

    for chunk in chunks:
        r = await translate(chunk, target_lang, detected_lang, engine)
        translated_parts.append(r.translated_text)
        if detected_lang == "auto":
            detected_lang = r.source_lang

    full_text = "\n".join(translated_parts)
    return TranslationResult(
        original_text="[chunked]",
        translated_text=full_text,
        source_lang=detected_lang,
        target_lang=target_lang,
        provider="chunked",
        char_count=sum(len(c) for c in chunks),
    )
