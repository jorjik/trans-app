"""
Tests for start.py — /start command and UI language selection.

Run: cd bot && python -m pytest tests/test_start.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from handlers.start import cmd_start, cb_set_ui_lang

from conftest import make_message, make_callback, FakeUserData


class TestCmdStart:
    """Tests for /start command."""

    @pytest.mark.asyncio
    async def test_start_always_shows_lang_picker_new_user(self, monkeypatch, patch_settings):
        """New user should see language selection."""
        fake_user = FakeUserData(telegram_id=123)
        async def fake_get_user(tg_id):
            return fake_user
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/start", from_id=123)
        msg.text = "/start"
        msg.from_user.language_code = "ru"

        await cmd_start(msg, MagicMock(args=None))

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Welcome" in call_text or "Добро пожаловать" in call_text
        assert "Choose your interface language" in call_text

    @pytest.mark.asyncio
    async def test_start_always_shows_lang_picker_existing_user(self, monkeypatch, patch_settings):
        """Existing user should ALSO see language selection (not main menu)."""
        fake_user = FakeUserData(telegram_id=123, ui_language="ru", target_language="de")
        async def fake_get_user(tg_id):
            return fake_user
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/start", from_id=123)
        msg.text = "/start"
        msg.from_user.language_code = "ru"

        await cmd_start(msg, MagicMock(args=None))

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        # Should show welcome/language picker, NOT the greeting with balance
        assert "Welcome" in call_text or "Добро пожаловать" in call_text
        assert "Hello" not in call_text  # from en locale start_greeting

    @pytest.mark.asyncio
    async def test_start_detects_telegram_language(self, monkeypatch, patch_settings):
        """Should detect user's Telegram language and pre-select it."""
        from keyboards.inline_kb import ui_lang_kb

        fake_user = FakeUserData(telegram_id=123)
        async def fake_get_user(tg_id):
            return fake_user
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        # User has 'uk' language in Telegram
        msg = make_message("/start", from_id=123, language_code="uk")
        msg.text = "/start"

        await cmd_start(msg, MagicMock(args=None))

        msg.answer.assert_called_once()
        # The keyboard should have 'uk' pre-selected
        # We can check that answer was called with a reply_markup
        reply_markup = msg.answer.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_start_fallback_language(self, monkeypatch, patch_settings):
        """Unknown Telegram language should fall back to 'en'."""
        fake_user = FakeUserData(telegram_id=123)
        async def fake_get_user(tg_id):
            return fake_user
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/start", from_id=123, language_code="fr")
        msg.text = "/start"

        await cmd_start(msg, MagicMock(args=None))

        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_pay_argument_triggers_checkout(self, monkeypatch, patch_settings):
        """/start pay_... should trigger checkout, not language selector."""
        fake_checkout = AsyncMock()
        # start_checkout is imported INSIDE cmd_start, so patch at services level
        monkeypatch.setattr("services.billing.start_checkout", fake_checkout)

        msg = make_message("/start pay_starter", from_id=123)
        msg.text = "/start pay_starter"
        command = MagicMock()
        command.args = "pay_starter"

        await cmd_start(msg, command)

        fake_checkout.assert_called_once()
        # Language picker should NOT be shown
        msg.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_pay_with_underscore_in_plan(self, monkeypatch, patch_settings):
        """/start pay_plan_id should parse plan correctly even with underscores."""
        fake_checkout = AsyncMock()
        monkeypatch.setattr("services.billing.start_checkout", fake_checkout)

        msg = make_message("/start pay_starter_plus", from_id=123)
        msg.text = "/start pay_starter_plus"
        command = MagicMock()
        command.args = "pay_starter_plus"

        await cmd_start(msg, command)

        fake_checkout.assert_called_once()
        # plan_id should be "starter" (first part before underscore after pay_)
        plan_arg = fake_checkout.call_args[0][1]
        assert plan_arg == "starter"


class TestSetUiLang:
    """Tests for cb_set_ui_lang callback."""

    @pytest.mark.asyncio
    async def test_set_ui_lang_new_user_shows_main_menu(self, monkeypatch, patch_settings):
        """After selecting UI language, new user should see main menu with greeting."""
        # Mock sync functions
        monkeypatch.setattr("handlers.start.sync_ui_language", AsyncMock(return_value=True))
        monkeypatch.setattr("handlers.start._sync_ui_lang", AsyncMock())

        # Mock get_user to return updated user with ui_language set
        called = []
        async def fake_get_user(tg_id):
            if not called:
                called.append(1)
                return FakeUserData(telegram_id=123, ui_language="")  # before
            return FakeUserData(telegram_id=123, ui_language="ru", target_language="es")  # after
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("set_ui_lang:ru", from_id=123)
        await cb_set_ui_lang(cb)

        cb.answer.assert_called_once()
        cb.message.edit_text.assert_called_once()
        # Should show greeting
        call_text = cb.message.edit_text.call_args[0][0]
        assert "Hi" in call_text or "Привет" in call_text

    @pytest.mark.asyncio
    async def test_set_ui_lang_existing_user_shows_main_menu(self, monkeypatch, patch_settings):
        """After changing UI language, show main menu."""
        monkeypatch.setattr("handlers.start.sync_ui_language", AsyncMock(return_value=True))
        monkeypatch.setattr("handlers.start._sync_ui_lang", AsyncMock())

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="uk", target_language="de",
                                chars_used=500, chars_remaining=49500)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("set_ui_lang:uk", from_id=123)
        await cb_set_ui_lang(cb)

        cb.answer.assert_called_once()
        cb.message.edit_text.assert_called_once()
        # Should update the language and show main menu
        call_text = cb.message.edit_text.call_args[0][0]
        assert "Hi" in call_text or "Привіт" in call_text

    @pytest.mark.asyncio
    async def test_set_ui_lang_uk_calls_sync_api(self, monkeypatch, patch_settings):
        """Changing UI language should call sync_ui_language and _sync_ui_lang (API)."""
        mock_sync = AsyncMock(return_value=True)
        mock_sync_api = AsyncMock()
        monkeypatch.setattr("handlers.start.sync_ui_language", mock_sync)
        monkeypatch.setattr("handlers.start._sync_ui_lang", mock_sync_api)

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="uk", target_language="es")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("set_ui_lang:uk", from_id=123)
        await cb_set_ui_lang(cb)

        # Should sync to storage and backend API
        mock_sync.assert_called_once_with(123, "uk")
        mock_sync_api.assert_called_once_with(123, "uk")
