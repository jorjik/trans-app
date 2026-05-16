"""Translation router вЂ” РІС‹Р±РѕСЂ РїСЂРѕРІР°Р№РґРµСЂР° Рё fallback."""

import logging
import time
from typing import Optional

from .base import BaseTranslationProvider, TranslationResult
from .google import GoogleFreeProvider
from .deepl import DeepLProvider
from services.cache import get_cached_translation, set_cached_translation

logger = logging.getLogger(__name__)

_providers: dict[str, BaseTranslationProvider] = {
    "google_free": GoogleFreeProvider(),
    "deepl": DeepLProvider(),
}


def _pick_provider(engine: str, target_lang: str) -> list[BaseTranslationProvider]:
    if engine != "auto":
        p = _providers.get(engine)
        if p and p.is_available():
            return [p, _providers["google_free"]]
    deepl = _providers["deepl"]
    google = _providers["google_free"]
    if deepl.is_available() and deepl.supports_language(target_lang):
        return [deepl, google]
    return [google]


async def translate(
    text: str,
    target_lang: str,
    source_lang: str = "auto",
    engine: str = "auto",
) -> TranslationResult:
    text = text.strip()
    if not text:
        raise ValueError("Empty text")

    cached = await get_cached_translation(text, source_lang, target_lang, engine)
    if cached:
        return TranslationResult(
            original_text=text,
            translated_text=cached["translated_text"],
            source_lang=cached["source_lang"],
            target_lang=target_lang,
            provider=cached["provider"],
            cached=True,
        )

    providers = _pick_provider(engine, target_lang)
    last_error: Optional[Exception] = None

    for provider in providers:
        try:
            t0 = time.monotonic()
            result = await provider.translate(text, target_lang, source_lang)
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.info("Translated via %s in %dms (%d chars)", provider.name, latency_ms, result.char_count)

            await set_cached_translation(
                text, source_lang, target_lang, engine,
                {"translated_text": result.translated_text, "source_lang": result.source_lang, "provider": result.provider},
            )
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.warning("Provider %s failed: %s", provider.name, e)
            last_error = e
            continue

    raise RuntimeError(f"All providers failed. Last: {last_error}")


async def translate_batch(texts: list[str], target_lang: str, source_lang: str = "auto", engine: str = "auto") -> list[TranslationResult]:
    import asyncio
    return await asyncio.gather(*[translate(t, target_lang, source_lang, engine) for t in texts])