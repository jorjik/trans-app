"""
Tests for storage.py and api_client.py — user data operations.

Run: cd bot && python -m pytest tests/test_storage.py -v
"""

import asyncio
import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock

from services.storage import get_user, deduct_chars, set_target_language, sync_ui_language
from services.api_client import UserData, _cache, _cache_set, _cache_get, _cache_invalidate
from conftest import FakeUserData


class TestUserDataModel:
    """Tests for UserData dataclass."""

    def test_default_values(self):
        user = UserData(telegram_id=123)
        assert user.telegram_id == 123
        assert user.target_language == "en"
        assert user.ui_language == ""
        assert user.favorite_langs == ["en", "de", "fr"]
        assert user.plan == "free"
        assert user.chars_limit == 25_000
        assert user.chars_used == 0
        assert user.chars_remaining == 25_000

    def test_is_quota_exceeded_false(self):
        user = UserData(telegram_id=123, chars_used=100, chars_limit=50000)
        assert user.is_quota_exceeded is False

    def test_is_quota_exceeded_true(self):
        user = UserData(telegram_id=123, chars_used=50000, chars_limit=50000)
        assert user.is_quota_exceeded is True

    def test_is_quota_exceeded_over_limit(self):
        user = UserData(telegram_id=123, chars_used=60000, chars_limit=50000)
        assert user.is_quota_exceeded is True

    def test_to_settings_dict(self):
        user = UserData(telegram_id=123, target_language="de", ui_language="ru")
        d = user.to_settings_dict()
        assert d["telegram_id"] == 123
        assert d["target_language"] == "de"
        assert d["ui_language"] == "ru"


class TestCache:
    """Tests for in-memory cache logic."""

    def setup_method(self):
        _cache.clear()

    def test_cache_set_get(self):
        user = UserData(telegram_id=123)
        _cache_set(123, user)
        cached = _cache_get(123)
        assert cached is not None
        assert cached.telegram_id == 123

    def test_cache_invalidate(self):
        user = UserData(telegram_id=123)
        _cache_set(123, user)
        _cache_invalidate(123)
        assert _cache_get(123) is None

    def test_cache_for_different_users(self):
        user1 = UserData(telegram_id=123, target_language="de")
        user2 = UserData(telegram_id=456, target_language="fr")
        _cache_set(123, user1)
        _cache_set(456, user2)

        assert _cache_get(123).target_language == "de"
        assert _cache_get(456).target_language == "fr"


class TestGetUser:
    """Tests for get_user with mocked HTTP."""

    def setup_method(self):
        _cache.clear()

    @pytest.mark.asyncio
    async def test_get_user_no_api_url(self, monkeypatch):
        """Without API URL, should return default user."""
        monkeypatch.setattr("config.settings.api_url", None)
        user = await get_user(123)
        assert user.telegram_id == 123
        assert user.target_language == "en"

    @pytest.mark.asyncio
    async def test_get_user_cached(self, monkeypatch):
        """Should return cached data without calling API."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")
        user = UserData(telegram_id=123, target_language="de")
        _cache_set(123, user)

        result = await get_user(123)
        assert result.target_language == "de"

    def _make_async_resp(self, status=200, json_data=None):
        """Create a mock HTTP response that supports async with."""
        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data or {})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        return mock_resp

    def _make_mock_session(self, monkeypatch, resp_or_error):
        """Create a mock session and patch it into api_client."""
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=resp_or_error)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)
        return mock_session

    @pytest.mark.asyncio
    async def test_get_user_api_success(self, monkeypatch):
        """API returns user data -> parse and cache."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")
        monkeypatch.setattr("config.settings.bot_internal_secret", "secret")

        mock_resp = self._make_async_resp(200, {
            "target_language": "fr",
            "ui_language": "ru",
            "favorite_langs": ["en", "de", "fr", "es"],
            "plan": "starter",
            "chars_limit": 500000,
            "chars_used": 1000,
            "chars_remaining": 499000,
            "reset_at": "2026-06-01T00:00:00",
        })
        self._make_mock_session(monkeypatch, mock_resp)

        result = await get_user(123)
        assert result.target_language == "fr"
        assert result.ui_language == "ru"
        assert result.plan == "starter"
        assert result.chars_limit == 500000
        assert result.chars_remaining == 499000

    @pytest.mark.asyncio
    async def test_get_user_api_404(self, monkeypatch):
        """API returns 404 -> create default user."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")

        mock_resp = self._make_async_resp(404)
        self._make_mock_session(monkeypatch, mock_resp)

        result = await get_user(999)
        assert result.telegram_id == 999
        assert result.target_language == "en"

    @pytest.mark.asyncio
    async def test_get_user_api_error_fallback_to_cache(self, monkeypatch):
        """API error -> fall back to cache, then default."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")

        # First, cache a user
        cached_user = UserData(telegram_id=123, target_language="pt")
        _cache_set(123, cached_user)

        # Then make API fail - use aiohttp.ClientError to match the except clause
        mock_resp = MagicMock()
        mock_resp.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection error"))
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        self._make_mock_session(monkeypatch, mock_resp)

        result = await get_user(123)
        assert result.target_language == "pt"


class TestDeductChars:
    """Tests for deduct_chars with mocked HTTP."""

    def setup_method(self):
        _cache.clear()

    @pytest.mark.asyncio
    async def test_deduct_no_api_url(self, monkeypatch):
        """Without API URL, should return None."""
        monkeypatch.setattr("config.settings.api_url", None)
        result = await deduct_chars(123, 100)
        assert result is None

    @pytest.mark.asyncio
    async def test_deduct_success(self, monkeypatch):
        """Successful deduction returns updated user."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")
        monkeypatch.setattr("config.settings.bot_internal_secret", "secret")

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "target_language": "en",
            "ui_language": "",
            "favorite_langs": ["en", "de", "fr"],
            "plan": "free",
            "chars_limit": 50000,
            "chars_used": 105,
            "chars_remaining": 49895,
        })
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)

        result = await deduct_chars(123, 5)
        assert result is not None
        assert result.chars_used == 105
        assert result.chars_remaining == 49895

    @pytest.mark.asyncio
    async def test_deduct_failure_invalidates_cache(self, monkeypatch):
        """Failed deduction should invalidate cache (aiohttp.ClientError)."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")

        # Cache something first
        _cache_set(123, UserData(telegram_id=123))
        assert _cache_get(123) is not None

        # Use aiohttp.ClientError so the except clause catches it
        mock_resp = MagicMock()
        mock_resp.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection timeout"))
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)

        result = await deduct_chars(123, 5)
        assert result is None
        # Cache should be invalidated
        assert _cache_get(123) is None


class TestSettingsUpdates:
    """Tests for set_target_language and sync_ui_language."""

    def setup_method(self):
        _cache.clear()

    @pytest.mark.asyncio
    async def test_set_target_language(self, monkeypatch):
        """set_target_language should update API and return user."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")
        monkeypatch.setattr("config.settings.bot_internal_secret", "secret")

        # Need a response that works for BOTH update_settings AND get_user calls
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "target_language": "de",
            "ui_language": "",
            "favorite_langs": ["en", "de", "fr"],
            "plan": "free",
            "chars_limit": 50000,
            "chars_used": 0,
            "chars_remaining": 50000,
        })
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)

        result = await set_target_language(123, "de")
        assert result is not None
        assert result.target_language == "de"

    @pytest.mark.asyncio
    async def test_sync_ui_language(self, monkeypatch):
        """sync_ui_language should sync UI language via API."""
        monkeypatch.setattr("config.settings.api_url", "http://test-api")
        monkeypatch.setattr("config.settings.bot_internal_secret", "secret")

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)

        result = await sync_ui_language(123, "ru")
        assert result is True

    @pytest.mark.asyncio
    async def test_sync_ui_language_no_api(self, monkeypatch):
        """Without API URL, sync should return False."""
        monkeypatch.setattr("config.settings.api_url", None)
        result = await sync_ui_language(123, "ru")
        assert result is False
