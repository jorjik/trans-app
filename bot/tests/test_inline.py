"""
Tests for inline.py — inline query handler.

Run: cd bot && python -m pytest tests/test_inline.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.inline import handle_inline_query
from conftest import FakeUserData


class TestHandleInlineQuery:
    """Tests for handle_inline_query."""

    @pytest.fixture
    def make_query(self, monkeypatch):
        """Factory for inline query mocks."""
        def _make(text="", from_id=123, language_code="ru"):
            query = AsyncMock()
            query.query = text
            query.from_user.id = from_id
            query.from_user.language_code = language_code
            query.answer = AsyncMock()
            return query
        return _make

    @pytest.mark.asyncio
    async def test_inline_empty_text_shows_placeholder(self, monkeypatch, patch_settings, make_query):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        query = make_query(text="")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1].get("results") == []
        assert "switch_pm_text" in query.answer.call_args[1]

    @pytest.mark.asyncio
    async def test_inline_short_text_shows_placeholder(self, monkeypatch, patch_settings, make_query):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        query = make_query(text="A")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1].get("results") == []

    @pytest.mark.asyncio
    async def test_inline_too_long(self, monkeypatch, patch_settings, make_query):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        query = make_query(text="A" * 1001)
        await handle_inline_query(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1].get("results") == []

    @pytest.mark.asyncio
    async def test_inline_quota_exceeded(self, monkeypatch, patch_settings, make_query):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en",
                                chars_used=50000, chars_limit=50000)
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        query = make_query(text="Hello world")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1].get("results") == []

    @pytest.mark.asyncio
    async def test_inline_successful_translation(self, monkeypatch, patch_settings, make_query):
        class FakeResult:
            translated_text = "Hola mundo"
            source_lang = "en"
            target_lang = "es"
            provider = "google"
            cached = False
            char_count = 11

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en",
                                favorite_langs=["es", "de", "fr"])
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        async def fake_translate(text, lang):
            return FakeResult()

        monkeypatch.setattr("handlers.inline.translate", fake_translate)

        query = make_query(text="Hello world")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        results = query.answer.call_args[1].get("results", [])
        assert len(results) > 0
        assert "Hola mundo" in results[0].description

    @pytest.mark.asyncio
    async def test_inline_no_translation_results(self, monkeypatch, patch_settings, make_query):
        """When all translations return exceptions, should show error message."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en",
                                favorite_langs=["es"])
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        async def fake_translate(text, lang):
            raise RuntimeError("Translation failed")

        monkeypatch.setattr("handlers.inline.translate", fake_translate)

        query = make_query(text="Hello")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        results = query.answer.call_args[1].get("results", [])
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_inline_same_text_filtered(self, monkeypatch, patch_settings, make_query):
        class FakeResult:
            translated_text = "hello"
            source_lang = "en"
            target_lang = "en"
            provider = "google"
            cached = False
            char_count = 5

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en",
                                favorite_langs=["en"])  # same language
        monkeypatch.setattr("handlers.inline.get_user", fake_get_user)

        async def fake_translate(text, lang):
            return FakeResult()

        monkeypatch.setattr("handlers.inline.translate", fake_translate)

        query = make_query(text="hello")
        await handle_inline_query(query)

        query.answer.assert_called_once()
        results = query.answer.call_args[1].get("results", [])
        assert len(results) == 0  # Should filter out same text
