"""
DeepL API провайдер.
Требует DEEPL_API_KEY. Free tier: 500k символов/мес.
"""

import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from services.translation.base import BaseTranslationProvider, TranslationResult

log = logging.getLogger(__name__)

# Языки поддерживаемые DeepL (source)
DEEPL_SOURCE_LANGS = {
    "ar", "bg", "cs", "da", "de", "el", "en", "es", "et", "fi",
    "fr", "hu", "id", "it", "ja", "ko", "lt", "lv", "nb", "nl",
    "pl", "pt", "ro", "ru", "sk", "sl", "sv", "tr", "uk", "zh",
}

# Target languages DeepL (чуть отличаются — en-us/en-gb, pt-br/pt-pt)
DEEPL_TARGET_LANGS = {
    "ar", "bg", "cs", "da", "de", "el", "en-gb", "en-us", "en",
    "es", "et", "fi", "fr", "hu", "id", "it", "ja", "ko", "lt",
    "lv", "nb", "nl", "pl", "pt-br", "pt-pt", "pt", "ro", "ru",
    "sk", "sl", "sv", "tr", "uk", "zh",
}

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"


class DeepLProvider(BaseTranslationProvider):
    name = "deepl"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.deepl_api_key
        if not self.api_key:
            raise ValueError("DEEPL_API_KEY not set")

        # Pro API если ключ не заканчивается на :fx
        if not self.api_key.endswith(":fx"):
            self._base_url = "https://api.deepl.com/v2/translate"
        else:
            self._base_url = DEEPL_API_URL

    def supports_language(self, lang_code: str) -> bool:
        code = lang_code.lower()
        return code in DEEPL_TARGET_LANGS or code == "auto"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        # DeepL не принимает "auto" — просто не передаём source_lang
        payload: dict = {
            "text": [text],
            "target_lang": target_lang.upper().replace("-", "_"),
        }
        if source_lang != "auto":
            payload["source_lang"] = source_lang.upper()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._base_url,
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                json=payload,
            )

        if resp.status_code == 456:
            raise RuntimeError("DeepL quota exceeded")
        if resp.status_code == 429:
            raise RuntimeError("DeepL rate limit")
        if resp.status_code != 200:
            raise RuntimeError(f"DeepL error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        translation = data["translations"][0]

        return TranslationResult(
            original_text=text,
            translated_text=translation["text"],
            source_lang=translation.get("detected_source_language", source_lang).lower(),
            target_lang=target_lang.lower(),
            provider=self.name,
        )
