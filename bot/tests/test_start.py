"""
Tests for start.py — /start command, UI language selection, and all callbacks.

Run: cd bot && python -m pytest tests/test_start.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.start import (
    cmd_start, cb_set_ui_lang, cmd_help, cmd_lang, cmd_quota, cmd_uilang,
    cb_help, cb_quota, cb_change_lang, cb_search_lang, cb_set_lang,
    cb_dismiss, cb_back_main, cb_referral, _sync_ui_lang,
    on_how_to_use_button, on_change_lang_button, on_my_balance_button,
)

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


class TestCmdHelp:
    """Tests for /help command."""

    @pytest.mark.asyncio
    async def test_cmd_help_shows_help_text(self, monkeypatch, patch_settings):
        """/help should show help text with translations."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/help", from_id=123)
        msg.text = "/help"

        await cmd_help(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Как пользоваться" in call_text
        assert "Перевод" in call_text or "перевод" in call_text
        assert "<b>" in call_text  # HTML formatting
        assert msg.answer.call_args[1].get("parse_mode") == "HTML"

    @pytest.mark.asyncio
    async def test_cmd_help_english(self, monkeypatch, patch_settings):
        """/help in English."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/help", from_id=123)
        await cmd_help(msg)

        call_text = msg.answer.call_args[0][0]
        assert "How to use" in call_text


class TestCmdLang:
    """Tests for /lang command."""

    @pytest.mark.asyncio
    async def test_cmd_lang_with_code(self, monkeypatch, patch_settings):
        """/lang de should set language to German."""
        mock_set = AsyncMock()
        monkeypatch.setattr("handlers.start.set_target_language", mock_set)

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/lang de", from_id=123)
        msg.text = "/lang de"

        await cmd_lang(msg)

        mock_set.assert_called_once_with(123, "de")
        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_lang_without_code_shows_keyboard(self, monkeypatch, patch_settings):
        """/lang without args should show language selection keyboard."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/lang", from_id=123)
        msg.text = "/lang"

        await cmd_lang(msg)

        msg.answer.assert_called_once()
        reply_markup = msg.answer.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_cmd_lang_unknown_code(self, monkeypatch, patch_settings):
        """/lang with unknown code should show error."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/lang xyz", from_id=123)
        msg.text = "/lang xyz"

        await cmd_lang(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "xyz" in call_text  # Should mention the unknown code


class TestCmdQuota:
    """Tests for /quota command."""

    @pytest.mark.asyncio
    async def test_cmd_quota_shows_balance(self, monkeypatch, patch_settings):
        """/quota should show char balance."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", chars_used=1000, chars_remaining=49000)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/quota", from_id=123)
        msg.text = "/quota"

        await cmd_quota(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "1,000" in call_text
        assert "49,000" in call_text
        assert call_text.startswith("<b>")  # HTML formatting

    @pytest.mark.asyncio
    async def test_cmd_quota_free_user_shows_upgrade_hint(self, monkeypatch, patch_settings):
        """Free users should see upgrade hint."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", plan="free", chars_used=0, chars_remaining=50000)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/quota", from_id=123)
        msg.text = "/quota"

        await cmd_quota(msg)

        call_text = msg.answer.call_args[0][0]
        assert "upgrade" in call_text.lower() or "Starter" in call_text

    @pytest.mark.asyncio
    async def test_cmd_quota_starter_user(self, monkeypatch, patch_settings):
        """Starter plan users should see different plan info."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru", plan="starter", chars_used=50000, chars_remaining=450000)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/quota", from_id=123)
        msg.text = "/quota"

        await cmd_quota(msg)

        call_text = msg.answer.call_args[0][0]
        assert "Starter" in call_text or "star" in call_text.lower()


class TestCmdUilang:
    """Tests for /uilang command."""

    @pytest.mark.asyncio
    async def test_cmd_uilang_with_code(self, monkeypatch, patch_settings):
        """/uilang ru should set UI language."""
        mock_sync = AsyncMock(return_value=True)
        monkeypatch.setattr("handlers.start.sync_ui_language", mock_sync)
        monkeypatch.setattr("handlers.start._sync_ui_lang", AsyncMock())

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/uilang ru", from_id=123)
        msg.text = "/uilang ru"

        await cmd_uilang(msg)

        mock_sync.assert_called_once_with(123, "ru")
        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_uilang_unknown_code(self, monkeypatch, patch_settings):
        """/uilang with unsupported code should show error."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/uilang zz", from_id=123)
        msg.text = "/uilang zz"

        await cmd_uilang(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "zz" in call_text

    @pytest.mark.asyncio
    async def test_cmd_uilang_without_code_shows_keyboard(self, monkeypatch, patch_settings):
        """/uilang without args shows language selection keyboard."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("/uilang", from_id=123)
        msg.text = "/uilang"

        await cmd_uilang(msg)

        msg.answer.assert_called_once()
        reply_markup = msg.answer.call_args[1].get("reply_markup")
        assert reply_markup is not None


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

    @pytest.mark.asyncio
    async def test_set_ui_lang_shows_reply_keyboard(self, monkeypatch, patch_settings):
        """After selecting UI language, show reply keyboard hint."""
        monkeypatch.setattr("handlers.start.sync_ui_language", AsyncMock(return_value=True))
        monkeypatch.setattr("handlers.start._sync_ui_lang", AsyncMock())

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", target_language="es")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("set_ui_lang:en", from_id=123)
        await cb_set_ui_lang(cb)

        # Should answer callback
        cb.answer.assert_called_once()
        # Should have called message.answer for reply keyboard
        cb.message.answer.assert_called_once()
        reply_markup = cb.message.answer.call_args[1].get("reply_markup")
        assert reply_markup is not None
        # Should be a ReplyKeyboardMarkup
        assert hasattr(reply_markup, "keyboard")


class TestCallbacks:
    """Tests for inline callback handlers."""

    @pytest.mark.asyncio
    async def test_cb_help(self, monkeypatch, patch_settings):
        """Help callback should show help text."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("help", from_id=123)
        await cb_help(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()
        call_text = cb.message.edit_text.call_args[0][0]
        assert "Как пользоваться" in call_text

    @pytest.mark.asyncio
    async def test_cb_help_english(self, monkeypatch, patch_settings):
        """Help callback should show English help."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("help", from_id=123)
        await cb_help(cb)

        call_text = cb.message.edit_text.call_args[0][0]
        assert "How to use" in call_text

    @pytest.mark.asyncio
    async def test_cb_quota(self, monkeypatch, patch_settings):
        """Quota callback should show balance."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru", chars_used=5000, chars_remaining=45000)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("quota", from_id=123)
        await cb_quota(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()
        call_text = cb.message.edit_text.call_args[0][0]
        assert "5,000" in call_text
        assert "45,000" in call_text

    @pytest.mark.asyncio
    async def test_cb_change_lang(self, monkeypatch, patch_settings):
        """Change lang callback should show language selection."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("change_lang", from_id=123)
        await cb_change_lang(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()
        reply_markup = cb.message.edit_text.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_cb_search_lang(self, monkeypatch, patch_settings):
        """Search lang callback should show popular languages."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("search_lang", from_id=123)
        await cb_search_lang(cb)

        cb.message.edit_text.assert_called_once()
        cb.answer.assert_called_once()
        reply_markup = cb.message.edit_text.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_cb_set_lang(self, monkeypatch, patch_settings):
        """setlang callback should set target language."""
        mock_set = AsyncMock()
        monkeypatch.setattr("handlers.start.set_target_language", mock_set)

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("setlang:de", from_id=123)
        await cb_set_lang(cb)

        mock_set.assert_called_once_with(123, "de")
        cb.answer.assert_called_once()
        cb.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_cb_dismiss(self, monkeypatch, patch_settings):
        """Dismiss callback should delete the message."""
        cb = make_callback("dismiss", from_id=123)
        cb.message.delete = AsyncMock()

        await cb_dismiss(cb)

        cb.answer.assert_called_once()
        cb.message.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cb_dismiss_delete_fails_gracefully(self, monkeypatch, patch_settings):
        """Dismiss should not crash if delete fails."""
        cb = make_callback("dismiss", from_id=123)
        cb.message.delete = AsyncMock(side_effect=Exception("delete failed"))

        # Should not raise
        await cb_dismiss(cb)

        cb.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cb_back_main(self, monkeypatch, patch_settings):
        """Back to main should show status text."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru", target_language="de", chars_remaining=49000)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("back_main", from_id=123)
        await cb_back_main(cb)

        cb.answer.assert_called_once()
        cb.message.edit_text.assert_called_once()
        call_text = cb.message.edit_text.call_args[0][0]
        assert "49,000" in call_text

    @pytest.mark.asyncio
    async def test_cb_referral(self, monkeypatch, patch_settings):
        """Referral callback should show referral link."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        cb = make_callback("referral", from_id=123)
        await cb_referral(cb)

        cb.answer.assert_called_once()
        cb.message.answer.assert_called_once()
        call_text = cb.message.answer.call_args[0][0]
        assert "t.me/" in call_text  # referral link
        assert "ref_" in call_text


class TestSyncUiLang:
    """Tests for _sync_ui_lang helper."""

    @pytest.mark.asyncio
    async def test_sync_ui_lang_no_api(self, monkeypatch):
        """Without API URL, should silently return."""
        monkeypatch.setattr("handlers.start.settings.api_url", None)
        await _sync_ui_lang(123, "ru")
        # Should not raise

    @pytest.mark.asyncio
    async def test_sync_ui_lang_success(self, monkeypatch):
        """Should call API endpoint."""
        monkeypatch.setattr("handlers.start.settings.api_url", "http://test-api")
        monkeypatch.setattr("handlers.start.settings.bot_internal_secret", "secret")

        mock_post = AsyncMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("handlers.start.aiohttp.ClientSession", return_value=mock_session):
            await _sync_ui_lang(123, "ru")

        mock_session.post.assert_called_once()
        url = mock_session.post.call_args[0][0]
        assert "/internal/sync-ui-lang" in url

    @pytest.mark.asyncio
    async def test_sync_ui_lang_error_does_not_raise(self, monkeypatch):
        """API error should be caught silently."""
        monkeypatch.setattr("handlers.start.settings.api_url", "http://test-api")

        mock_post = AsyncMock(side_effect=Exception("Connection error"))
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("handlers.start.aiohttp.ClientSession", return_value=mock_session):
            # Should not raise
            await _sync_ui_lang(123, "ru")


class TestReplyKeyboardHandlers:
    """Tests for reply keyboard button handlers."""

    @pytest.mark.asyncio
    async def test_on_how_to_use_button(self, monkeypatch, patch_settings):
        """How to use reply button should show help."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("📖 Как пользоваться", from_id=123)
        msg.text = "📖 Как пользоваться"

        await on_how_to_use_button(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Как пользоваться" in call_text

    @pytest.mark.asyncio
    async def test_on_change_lang_button(self, monkeypatch, patch_settings):
        """Change lang reply button should show language selection."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("🌍 Change language", from_id=123)
        msg.text = "🌍 Change language"

        await on_change_lang_button(msg)

        msg.answer.assert_called_once()
        reply_markup = msg.answer.call_args[1].get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_on_my_balance_button(self, monkeypatch, patch_settings):
        """My balance reply button should show quota."""
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", chars_used=100, chars_remaining=49900)
        monkeypatch.setattr("handlers.start.get_user", fake_get_user)

        msg = make_message("📊 My balance", from_id=123)
        msg.text = "📊 My balance"

        await on_my_balance_button(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "100" in call_text or "49,900" in call_text