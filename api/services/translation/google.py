"""Google Translate (free tier через deep-translator, без API ключа)."""

import asyncio
import logging

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    TranslationNotFound,
)

from .base import BaseTranslationProvider, TranslationResult
from services.language_detect import detect_lang

logger = logging.getLogger(__name__)

# Языки поддерживаемые Google Translate
GOOGLE_SUPPORTED = {
    "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs",
    "bg", "ca", "ceb", "zh-cn", "zh-tw", "co", "hr", "cs", "da",
    "nl", "en", "eo", "et", "fi", "fr", "fy", "gl", "ka", "de",
    "el", "gu", "ht", "ha", "haw", "he", "iw", "hi", "hmn", "hu",
    "is", "ig", "id", "ga", "it", "ja", "jv", "kn", "kk", "km",
    "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk",
    "mg", "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no",
    "ny", "or", "ps", "fa", "pl", "pt", "pa", "ro", "ru", "sm",
    "gd", "sr", "st", "sn", "sd", "si", "sk", "sl", "so", "es",
    "su", "sw", "sv", "tl", "tg", "ta", "tt", "te", "th", "tr",
    "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu",
}


class GoogleFreeProvider(BaseTranslationProvider):
    name = "google_free"

    def is_available(self) -> bool:
        return True  # не требует API ключа

    def supports_language(self, lang_code: str) -> bool:
        return lang_code.lower() in GOOGLE_SUPPORTED

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        detected = source_lang
        if source_lang == "auto":
            detected = await detect_lang(text) or "auto"

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._translate_sync, text, target_lang, source_lang
        )
        result.source_lang = detected
        return result

    def _translate_sync(
        self, text: str, target_lang: str, source_lang: str
    ) -> TranslationResult:
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            if not translated:
                raise RuntimeError("Empty response from Google Translate")
            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
            )
        except LanguageNotSupportedException as e:
            raise ValueError(f"Language not supported by Google: {e}") from e
        except TranslationNotFound as e:
            raise RuntimeError(f"Translation not found: {e}") from e
        except Exception as e:
            logger.error("Google free translate error: %s", e)
            raise RuntimeError(str(e)) from e
