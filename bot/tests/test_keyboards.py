"""
Tests for inline_kb.py — all keyboard builder functions.

Run: cd bot && python -m pytest tests/test_keyboards.py -v
"""

import pytest

from keyboards.inline_kb import (
    main_menu_reply_kb, main_menu_kb, change_lang_kb, upgrade_kb,
    back_main_kb, translate_result_kb, popular_langs_kb, ui_lang_kb,
    admin_menu_kb, admin_payment_kb, billing_methods_kb,
)
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)


class TestMainMenuReplyKb:
    """Tests for main_menu_reply_kb() — reply keyboard."""

    def test_reply_kb_without_webapp(self):
        kb = main_menu_reply_kb("ru")
        assert isinstance(kb, ReplyKeyboardMarkup)
        # No WebApp button
        for row in kb.keyboard:
            for btn in row:
                assert btn.web_app is None

    def test_reply_kb_has_all_buttons(self):
        kb = main_menu_reply_kb("en")
        # Should have: How to use, Change language, My balance
        all_texts = [btn.text for row in kb.keyboard for btn in row]
        assert any("How" in t for t in all_texts)
        assert any("language" in t for t in all_texts)
        assert any("balance" in t for t in all_texts)

    def test_reply_kb_localized(self):
        kb_ru = main_menu_reply_kb("ru")
        kb_en = main_menu_reply_kb("en")
        ru_texts = [btn.text for row in kb_ru.keyboard for btn in row]
        en_texts = [btn.text for row in kb_en.keyboard for btn in row]
        assert any("Как пользоваться" in t for t in ru_texts)
        assert any("How" in t for t in en_texts)


class TestMainMenuKb:
    """Tests for main_menu_kb() — inline keyboard fallback."""

    def test_main_menu_inline(self):
        kb = main_menu_kb("https://example.com", "en")
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_main_menu_inline_buttons(self):
        kb = main_menu_kb(None, "en")
        # Should have 3 buttons: How to use, Change language, My balance
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 3


class TestChangeLangKb:
    """Tests for change_lang_kb()."""

    def test_change_lang_has_favorites(self):
        favs = ["en", "de", "fr"]
        kb = change_lang_kb(favs, "en")
        total = sum(len(row) for row in kb.inline_keyboard)
        # 3 favorites + Other + Back = 5 buttons
        assert total == 5

    def test_change_lang_has_back_and_other(self):
        kb = change_lang_kb(["en"], "en")
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Other" in t or "Другой" in t for t in texts)
        assert any("Back" in t or "Назад" in t for t in texts)


class TestUpgradeKb:
    """Tests for upgrade_kb()."""

    def test_upgrade_kb_buttons(self):
        kb = upgrade_kb("en")
        assert isinstance(kb, InlineKeyboardMarkup)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Starter" in t for t in texts)  # upgrade button
        assert any("Invite" in t or "друга" in t for t in texts)  # referral
        assert any("Back" in t or "Назад" in t for t in texts)

    def test_upgrade_kb_has_five_rows(self):
        kb = upgrade_kb("en")
        assert len(kb.inline_keyboard) == 5


class TestBackMainKb:
    """Tests for back_main_kb()."""

    def test_back_main_single_button(self):
        kb = back_main_kb("en")
        assert len(kb.inline_keyboard) == 1
        assert len(kb.inline_keyboard[0]) == 1
        assert kb.inline_keyboard[0][0].callback_data == "back_main"


class TestTranslateResultKb:
    """Tests for translate_result_kb()."""

    def test_translate_result_kb(self):
        kb = translate_result_kb("en", "ru", "Hello world", "en")
        assert isinstance(kb, InlineKeyboardMarkup)
        assert len(kb.inline_keyboard) == 1  # adjust(2) = 1 row
        assert len(kb.inline_keyboard[0]) == 2  # 2 buttons in a row
        cb_datas = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert any("retranslate" in d for d in cb_datas)
        assert any("dismiss" in d for d in cb_datas)


class TestAdminMenuKb:
    """Tests for admin_menu_kb()."""

    def test_admin_menu_has_three_buttons(self):
        kb = admin_menu_kb("en")
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 3  # Stats, Payment Methods, Back

    def test_admin_menu_has_stats_and_payment_callbacks(self):
        kb = admin_menu_kb("en")
        cbs = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "admin_stats" in cbs
        assert "admin_payment" in cbs
        assert "back_main" in cbs


class TestAdminPaymentKb:
    """Tests for admin_payment_kb()."""

    def test_admin_payment_has_four_buttons(self):
        config = {"stars": True, "kofi": True, "paypal": True}
        kb = admin_payment_kb(config, "en")
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 4  # 3 methods + Back

    def test_admin_payment_shows_checkmarks(self):
        config = {"stars": True, "kofi": False, "paypal": True}
        kb = admin_payment_kb(config, "en")
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Stars ✅" in t for t in texts)
        assert any("Ko-fi ❌" in t for t in texts)
        assert any("PayPal ✅" in t for t in texts)

    def test_admin_payment_toggle_callbacks(self):
        config = {"stars": True, "kofi": True, "paypal": True}
        kb = admin_payment_kb(config, "en")
        cbs = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "admin_toggle:stars" in cbs
        assert "admin_toggle:kofi" in cbs
        assert "admin_toggle:paypal" in cbs
        assert "admin_back" in cbs


class TestBillingMethodsKb:
    """Tests for billing_methods_kb()."""

    def test_all_visible_by_default(self):
        kb = billing_methods_kb("starter", "en")
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 4  # Stars, Ko-fi, PayPal, Back

    def test_filter_methods_with_visible_param(self):
        kb = billing_methods_kb("pro", "en", visible={"stars": True, "kofi": False, "paypal": False})
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Stars" in t for t in texts)
        assert not any("Ko-fi" in t for t in texts)
        assert not any("PayPal" in t for t in texts)

    def test_all_hidden_except_back(self):
        kb = billing_methods_kb("starter", "en", visible={"stars": False, "kofi": False, "paypal": False})
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 1  # Only Back

    def test_back_button_always_present(self):
        kb = billing_methods_kb("starter", "en", visible={"stars": False, "kofi": False, "paypal": False})
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Back" in t or "Назад" in t for t in texts)


class TestPopularLangsKb:
    """Tests for popular_langs_kb()."""

    def test_popular_langs_kb_default(self):
        kb = popular_langs_kb("en")
        assert isinstance(kb, InlineKeyboardMarkup)
        # 16 popular langs + 1 back button = 17 buttons
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 17

    def test_popular_langs_custom_prefix(self):
        kb = popular_langs_kb("en", callback_prefix="retranslate_to")
        for row in kb.inline_keyboard:
            for btn in row:
                if btn.callback_data != "change_lang":
                    assert btn.callback_data.startswith("retranslate_to:")

    def test_popular_langs_has_back(self):
        kb = popular_langs_kb("ru")
        last_btn = kb.inline_keyboard[-1][0]
        assert last_btn.callback_data == "change_lang"


class TestUiLangKb:
    """Tests for ui_lang_kb() — language selection for bot UI."""

    def test_ui_lang_kb_ten_langs(self):
        kb = ui_lang_kb("en")
        # adjust(2) = 5 rows of 2 buttons each
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 10  # 10 languages total
        # 10 buttons / 2 per row = 5 rows
        assert len(kb.inline_keyboard) == 5

    def test_ui_lang_kb_current_selected(self):
        kb_en = ui_lang_kb("en")
        assert "✅" in kb_en.inline_keyboard[0][0].text  # English (row 0, col 0) should have ✅

        kb_ru = ui_lang_kb("ru")
        assert "✅" in kb_ru.inline_keyboard[0][1].text  # Russian (row 0, col 1) should have ✅

        kb_de = ui_lang_kb("de")
        assert "✅" in kb_de.inline_keyboard[1][1].text  # German (row 1, col 1) should have ✅

    def test_ui_lang_kb_all_trigger_set_ui_lang(self):
        """All buttons should use set_ui_lang: callback data."""
        kb = ui_lang_kb("en")
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.callback_data.startswith("set_ui_lang:")
