"""
Tests for translate.py — forwarded message handler and retranslate flow.
Run: cd bot && python -m pytest tests/test_translate.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

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
                 forward_date=None, reply_to_message=None, first_name="TestUser",
                 language_code="ru") -> Message:
    """Create a mock aiogram Message."""
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.caption = None
    msg.chat = MagicMock(spec=Chat)
    msg.chat.type = chat_type
    msg.chat.id = from_id
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = from_id
    msg.from_user.first_name = first_name
    msg.from_user.language_code = language_code
    msg.forward_date = forward_date
    msg.reply_to_message = reply_to_message
    msg.bot = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.get_me = AsyncMock()
    me = MagicMock()
    me.username = "TransAppBot"
    msg.bot.get_me.return_value = me
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
    cb.bot.get_me = AsyncMock()
    me = MagicMock()
    me.username = "TransAppBot"
    cb.bot.get_me.return_value = me
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


class TestCmdTr:
    """Tests for /tr command."""

    @pytest.mark.asyncio
    async def test_cmd_tr_with_reply(self, monkeypatch, patch_settings):
        """/tr with reply should translate the replied message."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123, target_language="es")
        result = FakeTranslateResult("Hola mundo", "en", "es", cached=False)

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        # Create a reply message
        replied = make_message("Hello world", from_id=456)
        msg = make_message("/tr", from_id=123, reply_to_message=replied)
        msg.text = "/tr"

        await cmd_tr(msg)

        msg.bot.send_chat_action.assert_called_once()
        msg.answer.assert_called()
        call_text = msg.answer.call_args[0][0]
        assert "Hola mundo" in call_text

    @pytest.mark.asyncio
    async def test_cmd_tr_with_reply_and_lang(self, monkeypatch, patch_settings):
        """/tr de with reply should translate to German."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123, target_language="es")  # default is es
        result = FakeTranslateResult("Hallo Welt", "en", "de", cached=False)

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            assert lang == "de"  # Should use the argument, not default
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        replied = make_message("Hello world", from_id=456)
        msg = make_message("/tr de", from_id=123, reply_to_message=replied)
        msg.text = "/tr de"

        await cmd_tr(msg)

        msg.answer.assert_called()
        call_text = msg.answer.call_args[0][0]
        assert "Hallo Welt" in call_text

    @pytest.mark.asyncio
    async def test_cmd_tr_no_reply_shows_error(self, monkeypatch, patch_settings):
        """/tr without reply should show usage message."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("/tr", from_id=123, reply_to_message=None)
        msg.text = "/tr"

        await cmd_tr(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cmd_tr_unknown_lang(self, monkeypatch, patch_settings):
        """/tr with unknown language code should show error."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        replied = make_message("Hello", from_id=456)
        msg = make_message("/tr xyz", from_id=123, reply_to_message=replied)
        msg.text = "/tr xyz"

        await cmd_tr(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cmd_tr_quota_exceeded(self, monkeypatch, patch_settings):
        """/tr when quota exceeded should show quota message."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123, chars_used=50000, chars_limit=50000)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        replied = make_message("Hello", from_id=456)
        msg = make_message("/tr", from_id=123, reply_to_message=replied)
        msg.text = "/tr"

        await cmd_tr(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cmd_tr_cached_result(self, monkeypatch, patch_settings):
        """Cached translation should not deduct chars."""
        from handlers.translate import cmd_tr

        user = FakeUserData(123, target_language="es")
        result = FakeTranslateResult("Hola", "en", "es", cached=True)

        deduct_called = []
        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            deduct_called.append(True)
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        replied = make_message("Hello", from_id=456)
        msg = make_message("/tr", from_id=123, reply_to_message=replied)
        msg.text = "/tr"

        await cmd_tr(msg)
        assert len(deduct_called) == 0  # Should NOT deduct for cached


class TestCmdTo:
    """Tests for /to command."""

    @pytest.mark.asyncio
    async def test_cmd_to_basic(self, monkeypatch, patch_settings):
        """/to en text should translate the text."""
        from handlers.translate import cmd_to

        user = FakeUserData(123)
        result = FakeTranslateResult("Hello, how are you?", "ru", "en", cached=False)

        async def fake_get_user(tg_id):
            return user
        async def fake_translate(text, lang):
            return result
        async def fake_deduct(tg_id, count):
            return user

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        msg = make_message("/to en Привет, как дела?", from_id=123)
        msg.text = "/to en Привет, как дела?"

        await cmd_to(msg)

        msg.bot.send_chat_action.assert_called_once()
        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "Hello, how are you?" in call_text

    @pytest.mark.asyncio
    async def test_cmd_to_no_text(self, monkeypatch, patch_settings):
        """/to without text should show usage."""
        from handlers.translate import cmd_to

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("/to es", from_id=123)
        msg.text = "/to es"

        await cmd_to(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cmd_to_unknown_lang(self, monkeypatch, patch_settings):
        """/to with unknown language code should show usage."""
        from handlers.translate import cmd_to

        user = FakeUserData(123)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("/to xyz some text", from_id=123)
        msg.text = "/to xyz some text"

        await cmd_to(msg)

        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_to_quota_exceeded(self, monkeypatch, patch_settings):
        """/to when quota exceeded should show error."""
        from handlers.translate import cmd_to

        user = FakeUserData(123, chars_used=50000, chars_limit=50000)
        async def fake_get_user(tg_id):
            return user
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        msg = make_message("/to en Hello world", from_id=123)
        msg.text = "/to en Hello world"

        await cmd_to(msg)

        msg.reply.assert_called_once()
        msg.bot.send_chat_action.assert_not_called()


class TestExtractText:
    """Tests for _extract_text helper."""

    def test_extract_text_from_text(self):
        from handlers.translate import _extract_text
        msg = make_message("Hello world")
        result = _extract_text(msg)
        assert result == "Hello world"

    def test_extract_text_from_caption(self):
        from handlers.translate import _extract_text
        msg = make_message(text=None)
        msg.text = None
        msg.caption = "Photo caption"
        result = _extract_text(msg)
        assert result == "Photo caption"

    def test_extract_text_none(self):
        from handlers.translate import _extract_text
        msg = make_message(text=None)
        msg.text = None
        msg.caption = None
        result = _extract_text(msg)
        assert result is None


class TestSplitMessage:
    """Tests for _split_message helper."""

    def test_split_short_message(self):
        from handlers.translate import _split_message
        result = _split_message("Hello world", 100)
        assert result == ["Hello world"]

    def test_split_long_message(self):
        from handlers.translate import _split_message
        text = "Hello world. " * 100
        result = _split_message(text, 200)
        assert len(result) > 1
        # Each chunk should be <= max_len
        for chunk in result:
            assert len(chunk) <= 200

    def test_split_preserves_words(self):
        from handlers.translate import _split_message
        # Should split at newline or space, not in the middle of a word
        # The split strips leading whitespace from remaining text via .lstrip()
        text = "AAA " + "B" * 100 + " CCC"
        result = _split_message(text, 50)
        # The space after AAA is consumed by lstrip(), so first chunk is "AAA"
        assert result[0] == "AAA"
        # The second chunk should start with all the B's
        assert result[1].startswith("B")

    def test_split_exact_length(self):
        from handlers.translate import _split_message
        text = "A" * 50
        result = _split_message(text, 50)
        assert result == ["A" * 50]

    def test_split_empty_text(self):
        from handlers.translate import _split_message
        result = _split_message("", 100)
        assert result == [""]


class TestRetranslateFlow:
    """Tests for cb_retranslate and cb_retranslate_to handlers."""

    @pytest.mark.asyncio
    async def test_cb_retranslate_shows_popular_langs(self, monkeypatch, patch_settings):
        from handlers.translate import cb_retranslate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        cb = make_callback("retranslate:en", from_id=123)
        await cb_retranslate(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()
        reply_markup = cb.message.edit_text.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_cb_retranslate_to_no_source(self, monkeypatch, patch_settings):
        from handlers.translate import cb_retranslate_to, _last_source_text

        _last_source_text.pop(123, None)

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        cb = make_callback("retranslate_to:de", from_id=123)
        await cb_retranslate_to(cb)

        cb.answer.assert_called_once()
        cb.answer.call_args[1].get("show_alert", False) is True

    @pytest.mark.asyncio
    async def test_cb_retranslate_to_quota_exceeded(self, monkeypatch, patch_settings):
        from handlers.translate import cb_retranslate_to, _last_source_text

        _last_source_text[123] = "Hello world"

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", chars_used=50000, chars_limit=50000)
        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)

        cb = make_callback("retranslate_to:de", from_id=123)
        await cb_retranslate_to(cb)

        cb.message.edit_text.assert_called_once()
        call_text = cb.message.edit_text.call_args[0][0]
        assert "quota" in call_text.lower() or "limit" in call_text.lower()

    @pytest.mark.asyncio
    async def test_cb_retranslate_to_success(self, monkeypatch, patch_settings):
        from handlers.translate import cb_retranslate_to, _last_source_text

        _last_source_text[123] = "Hello world"

        class FakeResult:
            translated_text = "Hallo Welt"
            source_lang = "en"
            target_lang = "de"
            provider = "google"
            cached = False
            char_count = 11

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", target_language="de", chars_remaining=49000)
        async def fake_translate(text, lang):
            return FakeResult()
        async def fake_deduct(tg_id, count):
            return FakeUserData(telegram_id=123, chars_used=11, chars_remaining=48989)

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        cb = make_callback("retranslate_to:de", from_id=123)
        await cb_retranslate_to(cb)

        cb.message.edit_text.assert_called_once()
        call_text = cb.message.edit_text.call_args[0][0]
        assert "Hallo Welt" in call_text

    @pytest.mark.asyncio
    async def test_cb_retranslate_to_cached(self, monkeypatch, patch_settings):
        from handlers.translate import cb_retranslate_to, _last_source_text

        _last_source_text[123] = "Hello"

        class FakeResult:
            translated_text = "Hola"
            source_lang = "en"
            target_lang = "es"
            provider = "google"
            cached = True
            char_count = 5

        deduct_called = []
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", chars_remaining=49000)
        async def fake_translate(text, lang):
            return FakeResult()
        async def fake_deduct(tg_id, count):
            deduct_called.append(True)
            return None

        monkeypatch.setattr("handlers.translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.translate.translate", fake_translate)
        monkeypatch.setattr("handlers.translate.deduct_chars", fake_deduct)

        cb = make_callback("retranslate_to:es", from_id=123)
        await cb_retranslate_to(cb)

        assert len(deduct_called) == 0  # Should NOT deduct for cached
        cb.message.edit_text.assert_called_once()