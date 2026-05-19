"""
Интернационализация бота.
Загружает JSON-словари из locales/ и предоставляет функцию t().
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
_cache: dict[str, dict[str, str]] = {}


def _load_locale(lang: str) -> dict[str, str]:
    """Загружает JSON-словарь для языка (с кэшированием)."""
    if lang not in _cache:
        path = _LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            logger.warning("Locale file not found: %s, falling back to en", path)
            path = _LOCALES_DIR / "en.json"
        try:
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except Exception as e:
            logger.error("Failed to load locale %s: %s", lang, e)
            _cache[lang] = {}
    return _cache[lang]


def t(key: str, lang: str, **kwargs) -> str:
    """
    Возвращает переведённую строку по ключу.

    Аргументы:
        key: ключ строки в JSON-словаре (например "start_greeting")
        lang: код языка ("ru" или "en")
        **kwargs: значения для подстановки {placeholder}

    Пример:
        t("start_greeting", "ru", name="Анна", target_lang="🇬🇧 English")
    """
    locale = _load_locale(lang)
    text = locale.get(key)
    if text is None:
        # Fallback на английский
        fallback = _load_locale("en").get(key)
        if fallback is not None:
            text = fallback
        else:
            logger.warning("Missing i18n key: %s (lang=%s)", key, lang)
            return f"{{{key}}}"

    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            logger.warning("Missing format arg %s for key=%s lang=%s", e, key, lang)
    return text


# Plan emoji helper (shared across handlers)
PLAN_EMOJI = {"free": "🆓", "starter": "⭐", "pro": "💎", "business": "🏢"}


def plan_name(key: str, lang: str) -> str:
    """Возвращает локализованное название тарифа."""
    return t(f"plan_{key}", lang)
