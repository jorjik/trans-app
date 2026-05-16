"""DeepL API provider."""

import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseTranslationProvider, TranslationResult
from core.config import settings
from services.language_detect import detect_lang

logger = logging.getLogger(__name__)

DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"

# Языки поддерживаемые DeepL
DEEPL_SUPPORTED = {
    "ar", "bg", "cs", "da", "de", "el", "en", "es", "et", "fi",
    "fr", "hu", "id", "it", "ja", "ko", "lt", "lv", "nb", "nl",
    "pl", "pt", "ro", "ru", "sk", "sl", "sv", "tr", "uk", "zh",
}


class DeepLProvider(BaseTranslationProvider):
    name = "deepl"

    def __init__(self):
        self._api_key = settings.deepl_api_key
        # Free keys заканчиваются на :fx
        self._url = (
            DEEPL_FREE_URL if self._api_key and self._api_key.endswith(":fx")
            else DEEPL_PRO_URL
        )

    def is_available(self) -> bool:
        return bool(self._api_key)

    def supports_language(self, lang_code: str) -> bool:
        return lang_code.lower().split("-")[0] in DEEPL_SUPPORTED

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(RuntimeError),
    )
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        detected = source_lang
        if source_lang == "auto":
            detected = await detect_lang(text) or "auto"

        src = None if source_lang == "auto" else source_lang.upper()
        tgt = target_lang.upper()

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    self._url,
                    headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
                    json={
                        "text": [text],
                        "target_lang": tgt,
                        **({"source_lang": src} if src else {}),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                translated = data["translations"][0]["text"]
                detected_by_api = data["translations"][0].get("detected_source_language", "").lower()

                return TranslationResult(
                    original_text=text,
                    translated_text=translated,
                    source_lang=detected_by_api or detected,
                    target_lang=target_lang,
                    provider=self.name,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 456:
                    raise ValueError("DeepL quota exceeded")
                logger.error("DeepL HTTP error %s: %s", e.response.status_code, e)
                raise RuntimeError(f"DeepL error: {e.response.status_code}") from e
            except httpx.RequestError as e:
                raise RuntimeError(f"DeepL connection error: {e}") from e
