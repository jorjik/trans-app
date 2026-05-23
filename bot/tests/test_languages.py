"""
Tests for languages.py — language codes, aliases, flags, and detection.

Run: cd bot && python -m pytest tests/test_languages.py -v
"""

import pytest

from utils.languages import (
    resolve_lang, to_google_lang, get_lang_name, get_lang_flag,
    get_lang_label, detect_language, LANG_NAMES, LANG_FLAGS,
)


class TestResolveLang:
    """Tests for resolve_lang."""

    def test_resolve_iso_code(self):
        assert resolve_lang("en") == "en"
        assert resolve_lang("de") == "de"
        assert resolve_lang("fr") == "fr"
        assert resolve_lang("zh-cn") == "zh-cn"

    def test_resolve_uppercase(self):
        assert resolve_lang("EN") == "en"
        assert resolve_lang("RU") == "ru"

    def test_resolve_alias(self):
        assert resolve_lang("английский") == "en"
        assert resolve_lang("немецкий") == "de"
        assert resolve_lang("french") == "fr"
        assert resolve_lang("испанский") == "es"
        assert resolve_lang("ukrainian") == "uk"
        assert resolve_lang("китайский") == "zh-cn"
        assert resolve_lang("japanese") == "ja"
        assert resolve_lang("korean") == "ko"

    def test_resolve_short_codes(self):
        assert resolve_lang("eng") == "en"
        assert resolve_lang("rus") == "ru"
        assert resolve_lang("deu") == "de"
        assert resolve_lang("fra") == "fr"
        assert resolve_lang("spa") == "es"
        assert resolve_lang("zho") == "zh-cn"
        assert resolve_lang("jpn") == "ja"
        assert resolve_lang("kor") == "ko"

    def test_resolve_unknown(self):
        assert resolve_lang("xyz") is None
        assert resolve_lang("") is None
        assert resolve_lang("  ") is None

    def test_resolve_chinese_variants(self):
        assert resolve_lang("zh-cn") == "zh-cn"
        assert resolve_lang("zh-tw") == "zh-tw"
        assert resolve_lang("zh-hans") == "zh-cn"
        assert resolve_lang("zh-hant") == "zh-tw"

    def test_resolve_with_underscore(self):
        """Should normalize underscores to hyphens."""
        result = resolve_lang("zh_cn")
        assert result == "zh-cn"


class TestToGoogleLang:
    """Tests for to_google_lang."""

    def test_to_google_basic(self):
        assert to_google_lang("en") == "en"
        assert to_google_lang("de") == "de"

    def test_to_google_chinese(self):
        assert to_google_lang("zh-cn") == "zh-CN"
        assert to_google_lang("zh-tw") == "zh-TW"

    def test_to_google_hebrew(self):
        assert to_google_lang("he") == "iw"

    def test_to_google_fallback(self):
        assert to_google_lang("fr") == "fr"
        assert to_google_lang("es") == "es"


class TestGetLangName:
    """Tests for get_lang_name."""

    def test_get_name_basic(self):
        assert get_lang_name("en") == "English"
        assert get_lang_name("ru") == "Русский"
        assert get_lang_name("de") == "Deutsch"
        assert get_lang_name("fr") == "Français"

    def test_get_name_unknown(self):
        assert get_lang_name("xyz") == "XYZ"
        assert get_lang_name("") == ""

    def test_get_name_chinese(self):
        assert get_lang_name("zh-cn") == "中文 (简体)"


class TestGetLangFlag:
    """Tests for get_lang_flag."""

    def test_get_flag_basic(self):
        assert get_lang_flag("en") == "🇬🇧"
        assert get_lang_flag("ru") == "🇷🇺"
        assert get_lang_flag("de") == "🇩🇪"
        assert get_lang_flag("fr") == "🇫🇷"
        assert get_lang_flag("es") == "🇪🇸"

    def test_get_flag_unknown(self):
        assert get_lang_flag("xyz") == "🌐"


class TestGetLangLabel:
    """Tests for get_lang_label (flag + name)."""

    def test_get_label(self):
        label = get_lang_label("en")
        assert "🇬🇧" in label
        assert "English" in label

    def test_get_label_ru(self):
        label = get_lang_label("ru")
        assert "🇷🇺" in label
        assert "Русский" in label


class TestDetectLanguage:
    """Tests for detect_language using langdetect."""

    def test_detect_english(self):
        result = detect_language("The quick brown fox jumps over the lazy dog")
        assert result == "en"

    def test_detect_russian(self):
        result = detect_language("Здравствуйте! Меня зовут Александр, я из Москвы. Как у вас дела сегодня?")
        assert result == "ru"

    def test_detect_german(self):
        result = detect_language("Guten Tag, wie geht es Ihnen?")
        assert result == "de"

    def test_detect_french(self):
        result = detect_language("Bonjour, comment allez-vous?")
        assert result == "fr"

    def test_detect_spanish(self):
        result = detect_language("Hola, ¿cómo estás?")
        assert result == "es"

    def test_detect_short_text(self):
        """Very short text may return None or raise exception."""
        result = detect_language("Hi")
        # May be None or detect correctly — just ensure no crash
        assert result is None or isinstance(result, str)

    def test_detect_empty(self):
        result = detect_language("")
        assert result is None

    def test_detect_whitespace(self):
        result = detect_language("   ")
        assert result is None


class TestLangDataCompleteness:
    """Tests for completeness of language dictionaries."""

    def test_flag_count_matches_name_count(self):
        """Every named language should have a flag (or at least not crash)."""
        for code in LANG_NAMES:
            flag = get_lang_flag(code)
            assert flag  # should not be empty

    def test_popular_languages_have_flags(self):
        popular = ["en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk", "tr",
                   "ar", "zh-cn", "ja", "ko", "nl", "sv"]
        for code in popular:
            assert code in LANG_NAMES, f"{code} missing from LANG_NAMES"
            assert code in LANG_FLAGS, f"{code} missing from LANG_FLAGS"
