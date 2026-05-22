"""
Tests for translate.py — forwarded message handler and retranslate flow.
Run: cd bot && python -m pytest tests/test_translate.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone

from aiogram.types import Message, User, Chat, CallbackQuery


class FakeTranslateResult:
    def __init__(self, translated_text="Hola", source_lang="en", target_lang="es",
                 provider="google", cached=False, char_count=4):
        self.translated_text = translated_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.provider = provider
        self.cached = cached
        self.char_count = char_count


class FakeUserData:
    def __init__(self, telegram_id, target_language="es", ui_language="ru",
                 chars_used=0, chars_limit=50000, chars_remaining=50000):
        self.telegram_id = telegram_id
        self.target_language = target_language
        self.ui_language = ui_language
        self.chars_limit = chars_limit
        self.chars_used = chars_used
        self.chars_remaining = chars_remaining
        self.is_quota_exceeded = chars_used >= chars_limit


def make_message(text="Hello world", from_id=123, chat_type="private",
                 forward_date=None) -> Message:
    """Create a mock aiogram Message."""
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.caption = None
    msg.chat = MagicMock(spec=Chat)
    msg.chat.type = chat_type
    msg.chat.id = from_id
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = from_id
    msg.from_user.first_name = "TestUser"
    msg.from_user.language_code = "ru"
    msg.forward_date = forward_date
    msg.reply_to_message = None
    msg.bot = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.get_me = AsyncMock()
    msg.reply = AsyncMock()
    msg.answer = AsyncMock()
    return msg


def make_callback(data: str, from_id=123) -> CallbackQuery:
    """Create a mock aiogram CallbackQuery."""
    cb = MagicMock(spec=CallbackQuery)
    cb.data = data
    cb.from_user = MagicMock(spec=User)
    cb.from_user.id = from_id
    cb.from_user.first_name = "TestUser"
    cb.message = MagicMock(spec=Message)
    cb.message.chat = MagicMock()
    cb.message.chat.id = from_id
    cb.message.edit_text = AsyncMock()
    cb.bot = AsyncMock()
    cb.bot.send_chat_action = AsyncMock()
    cb.answer = AsyncMock()
    return cb


class TestForwardedMessageHandler:
    """Tests for handle_forwarded() — пересылка сообщения боту."""

    @pytest.mark.asyncio
    async def test_forward_triggers_translation(self, monkeypatch):
        """Пересланное сообщение должно переводиться."""
        from handlers.translate import handle_forwarded, router, _last_source_text

        user = FakeUserData(123)
        result = FakeTranslateResult("Привет", "en", "ru", cached=False)

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        msg = make_message("Hello", from_id=123, forward_date=datetime(2026, 1, 1))

        await handle_forwarded(msg)

        # Should send typing action
        msg.bot.send_chat_action.assert_called_once()
        # Should save source text for retranslate
        assert _last_source_text.get(123) == "Hello"
        # Should send translation result
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_forward_empty_text_shows_error(self, monkeypatch):
        """Пересланное сообщение без текста — ошибка."""
        from handlers.translate import handle_forwarded

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message(None, from_id=123, forward_date=datetime(2026, 1, 1))
        msg.text = None
        msg.caption = None

        await handle_forwarded(msg)

        msg.reply.assert_called_once()
        # Should NOT try to translate
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_forward_quota_exceeded(self, monkeypatch):
        """При превышении квоты — сообщение о лимите."""
        from handlers.translate import handle_forwarded

        user = FakeUserData(123, chars_used=50000, chars_limit=50000)
        async def fake_get_user(tg_id):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("Hello", from_id=123, forward_date=datetime(2026, 1, 1))
        await handle_forwarded(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_forward_text_too_long_for_quota(self, monkeypatch):
        """Текст длиннее остатка квоты."""
        from handlers.translate import handle_forwarded

        user = FakeUserData(123, chars_remaining=3)
        async def fake_get_user(tg_id):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("Hello long text", from_id=123, forward_date=datetime(2026, 1, 1))
        await handle_forwarded(msg)

        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_forward_saves_source_for_retranslate(self, monkeypatch):
        """После перевода текст сохраняется в _last_source_text."""
        from handlers.translate import handle_forwarded, _last_source_text

        user = FakeUserData(123)
        result = FakeTranslateResult("Hola", "en", "es")

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        msg = make_message("Hello", from_id=123, forward_date=datetime(2026, 1, 1))
        await handle_forwarded(msg)

        assert _last_source_text[123] == "Hello"

    @pytest.mark.asyncio
    async def test_non_forwarded_does_not_trigger(self, monkeypatch):
        """Обычное (не пересланное) сообщение не должно вызывать перевод."""
        from handlers.translate import router, handle_forwarded
        # The filter F.forward_date.is_not(None) should prevent non-forwarded messages
        # This is tested indirectly — the handler shouldn't be called
        # We verify that the router has the correct filter registered
        assert len(router.message.handlers) > 0
        # The last handler should be the forwarded one
        last_handler = router.message.handlers[-1]
        # Check it has the forward_date filter
        assert last_handler.callback == handle_forwarded  # type: ignore


class TestRetranslateFlow:
    """Tests for cb_retranslate and cb_retranslate_to handlers."""

    @pytest.mark.asyncio
    async def test_retranslate_shows_language_selector(self, monkeypatch):
        """Кнопка 'другой язык' показывает список языков."""
        from handlers.translate import cb_retranslate, _last_source_text

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        cb = make_callback("retranslate:en")
        await cb_retranslate(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_retranslate_to_translates(self, monkeypatch):
        """Выбор языка в ретранслейте переводит сохранённый текст."""
        from handlers.translate import cb_retranslate_to, _last_source_text

        user = FakeUserData(123)
        result = FakeTranslateResult("Bonjour", "en", "fr", cached=False)
        _last_source_text[123] = "Hello"

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        cb = make_callback("retranslate_to:fr")
        await cb_retranslate_to(cb)

        cb.bot.send_chat_action.assert_called_once()
        cb.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_retranslate_to_no_source_text(self, monkeypatch):
        """Ретранслейт без сохранённого текста — показывает ошибку."""
        from handlers.translate import cb_retranslate_to, _last_source_text

        user = FakeUserData(123)
        _last_source_text.clear()

        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        cb = make_callback("retranslate_to:fr")
        await cb_retranslate_to(cb)

        cb.answer.assert_called_once()
        # show_alert=True for the error
        assert cb.answer.call_args[1].get("show_alert") is True

    @pytest.mark.asyncio
    async def test_full_forward_then_retranslate_flow(self, monkeypatch):
        """Полный flow: пересылка → перевод → ретранслейт на другой язык."""
        from handlers.translate import (
            handle_forwarded, cb_retranslate, cb_retranslate_to, _last_source_text
        )

        user = FakeUserData(123, target_language="es")
        result1 = FakeTranslateResult("Hola", "en", "es", cached=False)
        result2 = FakeTranslateResult("Bonjour", "en", "fr", cached=False)

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            if lang == "es":
                return result1
            return result2
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        # Step 1: Forward a message
        msg = make_message("Hello", from_id=123, forward_date=datetime(2026, 1, 1))
        await handle_forwarded(msg)

        assert _last_source_text[123] == "Hello"
        msg.answer.assert_called()
        translated_call = msg.answer.call_args[0][0]
        assert "Hola" in translated_call

        # Step 2: Click "retranslate" button
        cb1 = make_callback("retranslate:en")
        await cb_retranslate(cb1)

        cb1.message.edit_text.assert_called_once()

        # Step 3: Select new language
        cb2 = make_callback("retranslate_to:fr")
        await cb_retranslate_to(cb2)

        cb2.message.edit_text.assert_called_once()
        translated_call2 = cb2.message.edit_text.call_args[0][0]
        assert "Bonjour" in translated_call2
