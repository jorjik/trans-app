"""
Google Translate (бесплатный, через deep-translator).
Без API-ключа. Для MVP — основной провайдер.
"""

import asyncio
import logging

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    TranslationNotFound,
)
from langdetect import detect, LangDetectException

from services.translation.base import BaseTranslationProvider, TranslationResult

log = logging.getLogger(__name__)

# Языки, поддерживаемые Google Translate
SUPPORTED_LANGS = {
    "af","sq","am","ar","hy","az","eu","be","bn","bs","bg","ca","ceb",
    "zh-cn","zh-tw","co","hr","cs","da","nl","en","eo","et","fi","fr",
    "fy","gl","ka","de","el","gu","ht","ha","haw","iw","hi","hmn","hu",
    "is","ig","id","ga","it","ja","jv","kn","kk","km","rw","ko","ku",
    "ky","lo","la","lv","lt","lb","mk","mg","ms","ml","mt","mi","mr",
    "mn","my","ne","no","ny","or","ps","fa","pl","pt","pa","ro","ru",
    "sm","gd","sr","st","sn","sd","si","sk","sl","so","es","su","sw",
    "sv","tl","tg","ta","tt","te","th","tr","tk","uk","ur","ug","uz",
    "vi","cy","xh","yi","yo","zu",
}


class GoogleFreeProvider(BaseTranslationProvider):
    name = "google_free"

    def supports_language(self, lang_code: str) -> bool:
        return lang_code.lower() in SUPPORTED_LANGS or lang_code == "auto"

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        # Определяем язык если auto
        detected = source_lang
        if source_lang == "auto":
            detected = await self._detect(text)

        translated = await asyncio.get_event_loop().run_in_executor(
            None, self._translate_sync, text, target_lang, source_lang
        )

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_lang=detected,
            target_lang=target_lang,
            provider=self.name,
        )

    def _translate_sync(self, text: str, target: str, source: str) -> str:
        try:
            translator = GoogleTranslator(source=source, target=target)
            result = translator.translate(text)
            if not result:
                raise RuntimeError("Empty translation result")
            return result
        except LanguageNotSupportedException as e:
            raise ValueError(f"Unsupported language: {e}") from e
        except TranslationNotFound as e:
            raise RuntimeError(f"Translation not found: {e}") from e
        except Exception as e:
            log.error("GoogleFree error: %s", e)
            raise RuntimeError(f"Translation failed: {e}") from e

    async def _detect(self, text: str) -> str:
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, detect, text
            )
        except LangDetectException:
            return "auto"
