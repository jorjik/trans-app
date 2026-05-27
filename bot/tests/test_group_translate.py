"""
Tests for group_translate.py — auto-translate in multilingual groups.

Run: cd bot && python -m pytest tests/test_group_translate.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from conftest import make_message, FakeUserData


class FakeGroupConfig:
    def __init__(self, exists=True, is_active=True, target_lang="en", translator_uid=1, chat_id=-100123, chat_title="Test Group"):
        self.exists = exists
        self.is_active = is_active
        self.target_lang = target_lang
        self.translator_uid = translator_uid
        self.chat_id = chat_id
        self.chat_title = chat_title

    def get(self, key, default=None):
        return getattr(self, key, default)


class FakeTranslateResult:
    def __init__(self, translated_text="Hello", source_lang="ru", target_lang="en",
                 provider="google", cached=False, char_count=5):
        self.translated_text = translated_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.provider = provider
        self.cached = cached
        self.char_count = char_count


class TestCmdGroupTranslate:
    """Tests for /group_translate command."""

    @pytest.mark.asyncio
    async def test_not_in_group(self, monkeypatch):
        """Command in private chat should show error."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate", from_id=123, chat_type="private")
        msg.text = "/group_translate"

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "group chats" in call_text.lower() or "only groups" in call_text.lower()

    @pytest.mark.asyncio
    async def test_not_admin(self, monkeypatch):
        """Non-admin user should get error."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate"
        msg.chat.title = "Test Group"

        # Mock get_chat_member to return non-admin
        chat_member = MagicMock()
        chat_member.status = "member"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "admin" in call_text.lower() or "administrator" in call_text.lower()

    @pytest.mark.asyncio
    async def test_status_enabled(self, monkeypatch):
        """Show status when group is active."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_get_group_config(chat_id):
            return {"exists": True, "is_active": True, "target_lang": "de", "translator_uid": 1}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.get_group_config", fake_get_group_config)

        msg = make_message("/group_translate", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "enabled" in call_text.lower() or "active" in call_text.lower()

    @pytest.mark.asyncio
    async def test_status_disabled(self, monkeypatch):
        """Show status when group is not active."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_get_group_config(chat_id):
            return {}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.get_group_config", fake_get_group_config)

        msg = make_message("/group_translate", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "disabled" in call_text.lower()

    @pytest.mark.asyncio
    async def test_turn_on(self, monkeypatch):
        """'/group_translate on' should enable translation."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_update_config(**kw):
            return {"status": "ok"}
        async def fake_refresh(chat_id):
            return {"exists": True, "is_active": True, "target_lang": "en", "translator_uid": 123}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.update_group_config", fake_update_config)
        monkeypatch.setattr("handlers.group_translate._refresh_group_cache", fake_refresh)

        msg = make_message("/group_translate on", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate on"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "creator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "enabled" in call_text.lower() or "activated" in call_text.lower()

    @pytest.mark.asyncio
    async def test_turn_on_with_lang(self, monkeypatch):
        """'/group_translate on de' should enable with German."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_update_config(**kw):
            return {"status": "ok"}
        async def fake_refresh(chat_id):
            return {"exists": True, "is_active": True, "target_lang": "de", "translator_uid": 123}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.update_group_config", fake_update_config)
        monkeypatch.setattr("handlers.group_translate._refresh_group_cache", fake_refresh)

        msg = make_message("/group_translate on de", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate on de"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "enabled" in call_text.lower() or "activated" in call_text.lower()

    @pytest.mark.asyncio
    async def test_turn_on_unknown_lang(self, monkeypatch):
        """'/group_translate on xyz' should show error."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate on xyz", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate on xyz"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "creator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, monkeypatch):
        """'/group_translate off' should disable translation."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_update_config(**kw):
            return {"status": "ok"}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.update_group_config", fake_update_config)

        msg = make_message("/group_translate off", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate off"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "disabled" in call_text.lower()

    @pytest.mark.asyncio
    async def test_target_lang(self, monkeypatch):
        """'/group_translate target fr' should change language."""
        from handlers.group_translate import cmd_group_translate, _active_groups
        _active_groups.clear()

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        async def fake_get_group_config(chat_id):
            return {"exists": True, "is_active": True, "target_lang": "en", "translator_uid": 123}
        async def fake_update_config(**kw):
            return {"status": "ok"}
        async def fake_refresh(chat_id):
            return {"exists": True, "is_active": True, "target_lang": "fr", "translator_uid": 123}

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.get_group_config", fake_get_group_config)
        monkeypatch.setattr("handlers.group_translate.update_group_config", fake_update_config)
        monkeypatch.setattr("handlers.group_translate._refresh_group_cache", fake_refresh)

        msg = make_message("/group_translate target fr", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate target fr"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()
        call_text = msg.reply.call_args[0][0]
        assert "changed" in call_text.lower() or "target" in call_text.lower()

    @pytest.mark.asyncio
    async def test_target_lang_no_arg(self, monkeypatch):
        """'/group_translate target' without language should show usage."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate target", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate target"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_target_lang_unknown(self, monkeypatch):
        """'/group_translate target xyz' should show error."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate target xyz", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate target xyz"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_subcommand(self, monkeypatch):
        """Unknown subcommand should show usage."""
        from handlers.group_translate import cmd_group_translate

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("/group_translate foo", from_id=123, chat_type="group", chat_id=-100)
        msg.text = "/group_translate foo"
        msg.chat.title = "Test Group"

        chat_member = MagicMock()
        chat_member.status = "administrator"
        msg.bot.get_chat_member = AsyncMock(return_value=chat_member)

        await cmd_group_translate(msg)

        msg.reply.assert_called_once()


class TestOnGroupMessage:
    """Tests for on_group_message — the message interceptor."""

    @pytest.mark.asyncio
    async def test_active_group_translates(self, monkeypatch):
        """Message in active group should be translated."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        # Pre-populate cache
        _active_groups[-100] = {
            "exists": True, "is_active": True,
            "target_lang": "en", "translator_uid": 1,
        }

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=1, chars_remaining=50000)
        async def fake_translate(text, lang):
            return FakeTranslateResult("Hello", "ru", "en", cached=False)
        async def fake_deduct(tg_id, count):
            return FakeUserData(telegram_id=1, chars_used=5, chars_remaining=49995)

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.do_translate", fake_translate)
        monkeypatch.setattr("handlers.group_translate.deduct_chars", fake_deduct)

        msg = make_message("Привет мир", from_id=555, chat_type="group", chat_id=-100)
        msg.text = "Привет мир"
        msg.from_user.is_bot = False
        msg.chat.title = "Test Group"

        await on_group_message(msg)

        msg.bot.send_chat_action.assert_called_once()
        msg.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_inactive_group_skips(self, monkeypatch):
        """Message in inactive group should not be translated."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        # No cache for this group -> should check API and find nothing
        async def fake_get_group_config(chat_id):
            return None

        monkeypatch.setattr("handlers.group_translate.get_group_config", fake_get_group_config)

        msg = make_message("Hello", from_id=555, chat_type="group", chat_id=-200)
        msg.text = "Hello"
        msg.from_user.is_bot = False

        await on_group_message(msg)

        msg.bot.send_chat_action.assert_not_called()
        msg.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_message_skipped(self, monkeypatch):
        """Bot messages should be skipped."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        _active_groups[-100] = {
            "exists": True, "is_active": True,
            "target_lang": "en", "translator_uid": 1,
        }

        msg = make_message("I am a bot", from_id=999, chat_type="group", chat_id=-100)
        msg.text = "I am a bot"
        msg.from_user.is_bot = True

        await on_group_message(msg)

        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_quota_exceeded_skips(self, monkeypatch):
        """When admin quota exceeded, skip translation."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        _active_groups[-100] = {
            "exists": True, "is_active": True,
            "target_lang": "en", "translator_uid": 1,
        }

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=1, chars_used=50000, chars_limit=50000)

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)

        msg = make_message("Hello world", from_id=555, chat_type="group", chat_id=-100)
        msg.text = "Hello world"
        msg.from_user.is_bot = False

        await on_group_message(msg)

        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_warming(self, monkeypatch):
        """Cache miss should fetch from API."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        async def fake_get_group_config(chat_id):
            return {
                "exists": True, "is_active": True,
                "target_lang": "es", "translator_uid": 1,
            }

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=1, chars_remaining=50000)
        async def fake_translate(text, lang):
            return FakeTranslateResult("Hola", "ru", "es", cached=False)
        async def fake_deduct(tg_id, count):
            return FakeUserData(telegram_id=1, chars_used=5)

        monkeypatch.setattr("handlers.group_translate.get_group_config", fake_get_group_config)
        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.do_translate", fake_translate)
        monkeypatch.setattr("handlers.group_translate.deduct_chars", fake_deduct)

        msg = make_message("Привет", from_id=555, chat_type="group", chat_id=-100)
        msg.text = "Привет"
        msg.from_user.is_bot = False
        msg.chat.title = "Test Group"

        await on_group_message(msg)

        # Should have cached the config
        assert -100 in _active_groups
        msg.bot.send_chat_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_short_text_skipped(self, monkeypatch):
        """Very short text (< 2 chars) should be skipped."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        _active_groups[-100] = {
            "exists": True, "is_active": True,
            "target_lang": "en", "translator_uid": 1,
        }

        msg = make_message("A", from_id=555, chat_type="group", chat_id=-100)
        msg.text = "A"
        msg.from_user.is_bot = False

        await on_group_message(msg)

        msg.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_translation_does_not_deduct(self, monkeypatch):
        """Cached translation should not deduct chars."""
        from handlers.group_translate import on_group_message, _active_groups
        _active_groups.clear()

        _active_groups[-100] = {
            "exists": True, "is_active": True,
            "target_lang": "en", "translator_uid": 1,
        }

        deduct_called = []

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=1, chars_remaining=50000)
        async def fake_translate(text, lang):
            return FakeTranslateResult("Hello", "ru", "en", cached=True)
        async def fake_deduct(tg_id, count):
            deduct_called.append(True)
            return None

        monkeypatch.setattr("handlers.group_translate.get_user", fake_get_user)
        monkeypatch.setattr("handlers.group_translate.do_translate", fake_translate)
        monkeypatch.setattr("handlers.group_translate.deduct_chars", fake_deduct)

        msg = make_message("Привет", from_id=555, chat_type="group", chat_id=-100)
        msg.text = "Привет"
        msg.from_user.is_bot = False

        await on_group_message(msg)

        assert len(deduct_called) == 0
        msg.reply.assert_called_once()


class TestBotAdded:
    """Tests for on_bot_added and on_bot_removed."""

    @pytest.mark.asyncio
    async def test_bot_added_to_group(self, monkeypatch):
        """Bot added to group should send welcome message."""
        from handlers.group_translate import on_bot_added

        event = MagicMock()
        event.chat.type = "group"
        event.chat.id = -100
        event.bot.send_message = AsyncMock()

        await on_bot_added(event)

        event.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_added_to_private_ignored(self, monkeypatch):
        """Bot added to private chat should be ignored."""
        from handlers.group_translate import on_bot_added

        event = MagicMock()
        event.chat.type = "private"
        event.chat.id = 123
        event.bot.send_message = AsyncMock()

        await on_bot_added(event)

        event.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_removed_clears_cache(self, monkeypatch):
        """Bot removed from group should clear cache."""
        from handlers.group_translate import on_bot_removed, _active_groups

        _active_groups[-100] = {"exists": True}
        _active_groups[-200] = {"exists": True}

        event = MagicMock()
        event.chat.id = -100

        await on_bot_removed(event)

        assert -100 not in _active_groups
        assert -200 in _active_groups  # other groups preserved


class TestRouterRegistration:
    """Tests that the router is properly set up."""

    def test_router_has_handlers(self):
        from handlers.group_translate import router
        assert len(router.message.handlers) > 0
        assert len(router.my_chat_member.handlers) > 0

    def test_command_filter(self):
        from handlers.group_translate import router
        cmd_handler = router.message.handlers[0]
        # Should have Command filter
        filters = cmd_handler.filters
        assert filters is not None
