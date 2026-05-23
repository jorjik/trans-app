"""
Tests for translator.py — translation service, caching, and Google Translate wrapper.

Run: cd bot && python -m pytest tests/test_translator.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.translator import (
    TranslationResult, translate, get_cache_stats,
    _cache_key, _get_from_cache, _put_to_cache,
    _do_translate_sync, _memory_cache,
)
from services.translator import _translate_long


@pytest.fixture(autouse=True)
def clear_memory_cache():
    """Clear in-memory cache before each test."""
    _memory_cache.clear()


class TestTranslationResult:
    """Tests for TranslationResult dataclass."""

    def test_default_char_count(self):
        result = TranslationResult(
            original_text="Hello",
            translated_text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
        )
        assert result.char_count == 5  # len("Hello")

    def test_explicit_char_count(self):
        result = TranslationResult(
            original_text="Hello",
            translated_text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
            char_count=42,
        )
        assert result.char_count == 42


class TestCacheKey:
    """Tests for _cache_key function."""

    def test_cache_key_deterministic(self):
        k1 = _cache_key("Hello", "en", "es")
        k2 = _cache_key("Hello", "en", "es")
        assert k1 == k2

    def test_cache_key_different_text(self):
        k1 = _cache_key("Hello", "en", "es")
        k2 = _cache_key("World", "en", "es")
        assert k1 != k2

    def test_cache_key_length(self):
        key = _cache_key("Hello", "en", "es")
        assert len(key) == 32  # sha256 hex digest truncated


class TestCache:
    """Tests for in-memory and Redis cache operations."""

    @pytest.mark.asyncio
    async def test_get_from_cache_empty(self):
        result = await _get_from_cache("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_put_and_get_from_memory(self):
        result = TranslationResult(
            original_text="Hello",
            translated_text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
        )
        key = _cache_key("Hello", "en", "es")
        await _put_to_cache(key, result)

        cached = await _get_from_cache(key)
        assert cached is not None
        assert cached.translated_text == "Hola"
        assert cached.cached is True

    @pytest.mark.asyncio
    async def test_cache_eviction(self, monkeypatch):
        """Test that oldest entries are evicted when cache is full."""
        monkeypatch.setattr("services.translator.MAX_MEMORY_CACHE", 1)

        r1 = TranslationResult("A", "B", "en", "es", "google")
        r2 = TranslationResult("C", "D", "en", "fr", "google")

        k1 = _cache_key("A", "en", "es")
        k2 = _cache_key("C", "en", "fr")

        await _put_to_cache(k1, r1)
        await _put_to_cache(k2, r2)

        # First entry should be evicted
        cached1 = await _get_from_cache(k1)
        assert cached1 is None

        # Second entry should remain
        cached2 = await _get_from_cache(k2)
        assert cached2 is not None


class TestDoTranslateSync:
    """Tests for _do_translate_sync (synchronous Google Translate wrapper)."""

    def test_empty_text_raises(self):
        with pytest.raises(RuntimeError, match="Empty translation"):
            _do_translate_sync("", "en", "auto", "auto")


class TestTranslate:
    """Tests for the main translate() async function."""

    @pytest.mark.asyncio
    async def test_translate_empty_text(self, monkeypatch):
        with pytest.raises(ValueError, match="Empty text"):
            await translate("  ", "en")

    @pytest.mark.asyncio
    async def test_translate_cache_hit(self, monkeypatch):
        # Langdetect may detect "Hello" as Finnish ("fi"), so we mock it
        monkeypatch.setattr("services.translator.detect_language", lambda t: "en")

        cached_result = TranslationResult(
            original_text="Hello",
            translated_text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
            cached=True,
        )
        key = _cache_key("Hello", "en", "es")
        await _put_to_cache(key, cached_result)

        result = await translate("Hello", "es")
        assert result.translated_text == "Hola"
        assert result.cached is True

    @pytest.mark.asyncio
    async def test_translate_long_text(self, monkeypatch):
        """Test that long texts are chunked."""

        class FakeResult:
            def __init__(self, text="Hola"):
                self.translated_text = text
                self.source_lang = "en"
                self.target_lang = "es"
                self.provider = "google"
                self.cached = False
                self.char_count = 5

        calls = []
        async def fake_translate(text, lang, source_lang="auto"):
            calls.append((text, lang))
            return FakeResult(text=f"TR_{text[:10]}")

        monkeypatch.setattr("services.translator.translate", fake_translate)
        monkeypatch.setattr("services.translator.settings.translate_chunk_size", 10)

        result = await _translate_long("Hello World Long Text", "es", "auto")
        assert len(calls) > 1  # Should be split into multiple calls


class TestCacheStats:
    """Tests for get_cache_stats."""

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        stats = await get_cache_stats()
        assert "memory_size" in stats
        assert "memory_max" in stats
        assert "redis_available" in stats
        assert "redis_keys_approx" in stats
