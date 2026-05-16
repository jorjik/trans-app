"""РћРїСЂРµРґРµР»РµРЅРёРµ СЏР·С‹РєР° С‚РµРєСЃС‚Р° (Р»РѕРєР°Р»СЊРЅРѕ, Р±РµР· РІРЅРµС€РЅРёС… API)."""

import asyncio
import logging
from typing import Optional

from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


async def detect_lang(text: str) -> Optional[str]:
    """РћРїСЂРµРґРµР»СЏРµС‚ СЏР·С‹Рє С‚РµРєСЃС‚Р°. Р’РѕР·РІСЂР°С‰Р°РµС‚ ISO РєРѕРґ РёР»Рё None."""
    if len(text.strip()) < 3:
        return None
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _detect_sync, text)
        return result
    except Exception as e:
        logger.warning("Language detection failed: %s", e)
        return None


def _detect_sync(text: str) -> Optional[str]:
    try:
        return detect(text)
    except LangDetectException:
        return None