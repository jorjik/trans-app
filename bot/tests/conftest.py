"""
Shared test fixtures and helpers for bot tests.
Run: cd bot && python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from aiogram.types import Message, User, Chat, CallbackQuery


class FakeUserData:
    def __init__(self, telegram_id=123, target_language="es", ui_language="",
                 favorite_langs=None, plan="free",
                 chars_used=0, chars_limit=50000, chars_remaining=50000):
        self.telegram_id = telegram_id
        self.target_language = target_language
        self.ui_language = ui_language
        self.favorite_langs = favorite_langs or ["en", "de", "fr"]
        self.plan = plan
        self.chars_limit = chars_limit
        self.chars_used = chars_used
        self.chars_remaining = chars_remaining
        self.is_quota_exceeded = chars_used >= chars_limit


class FakeTranslateResult:
    def __init__(self, translated_text="Hola", source_lang="en", target_lang="es",
                 provider="google", cached=False, char_count=5):
        self.translated_text = translated_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.provider = provider
        self.cached = cached
        self.char_count = char_count


def make_message(text="Hello world", from_id=123, chat_type="private",
                 forward_date=None, first_name="TestUser", language_code="ru",
                 reply_to_message=None, chat_id=None) -> Message:
    """Create a mock aiogram Message."""
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.caption = None
    msg.chat = MagicMock(spec=Chat)
    msg.chat.type = chat_type
    msg.chat.id = chat_id or from_id
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


def make_callback(data: str, from_id=123, first_name="TestUser") -> CallbackQuery:
    """Create a mock aiogram CallbackQuery."""
    cb = MagicMock(spec=CallbackQuery)
    cb.data = data
    cb.from_user = MagicMock(spec=User)
    cb.from_user.id = from_id
    cb.from_user.first_name = first_name
    cb.message = MagicMock(spec=Message)
    cb.message.chat = MagicMock()
    cb.message.chat.id = from_id
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.bot = AsyncMock()
    cb.bot.send_chat_action = AsyncMock()
    cb.bot.get_me = AsyncMock()
    me = MagicMock()
    me.username = "TransAppBot"
    cb.bot.get_me.return_value = me
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def fake_user():
    """Fixture: returns a default FakeUserData."""
    return FakeUserData()


@pytest.fixture
def fake_user_with_ui_lang():
    """Fixture: returns a FakeUserData with ui_language set (existing user)."""
    return FakeUserData(ui_language="ru", target_language="es", chars_used=100, chars_remaining=49900)


@pytest.fixture
def patch_settings(monkeypatch):
    """Fixture: patches settings to testing defaults."""
    monkeypatch.setattr("config.settings.mini_app_url", "https://example.com/miniapp")
    monkeypatch.setattr("config.settings.api_url", "http://test-api")
    monkeypatch.setattr("config.settings.max_result_length", 4096)
    monkeypatch.setattr("config.settings.bot_internal_secret", "test-secret")
