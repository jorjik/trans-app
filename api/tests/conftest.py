"""Shared test fixtures and helpers for API tests.

Run: cd api && python -m pytest tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    """Patch all monobank settings to test defaults."""
    monkeypatch.setattr("core.config.settings.monobank_token", "test_mono_token_12345")
    monkeypatch.setattr("core.config.settings.monobank_currency", 980)
    monkeypatch.setattr("core.config.settings.monobank_amount_per_star", 0.02)
    monkeypatch.setattr("core.config.settings.monobank_webhook_url", "https://test.api/webhook/monobank")
    monkeypatch.setattr("core.config.settings.env", "test")


@pytest.fixture
def mock_aiohttp_response():
    """Factory fixture: creates a mock aiohttp response.

    Usage:
        mock_resp = mock_aiohttp_response(status=200, json_data={"key": "val"})
    """
    def _make_response(status: int = 200, json_data: dict = None, text: str = ""):
        resp = MagicMock()
        resp.status = status
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=None)

        async def _json():
            return json_data or {}

        async def _text():
            return text

        resp.json = _json
        resp.text = _text
        return resp

    return _make_response


@pytest.fixture
def mock_aiohttp_session(mock_aiohttp_response):
    """Fixture: creates a properly mocked aiohttp ClientSession.

    The session supports async context manager protocol and has
    configurable post/get methods.

    Usage:
        mock_session = mock_aiohttp_session(
            post_status=200,
            post_json={"invoiceId": "abc"},
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)
    """
    def _make_session(
        post_status: int = 200,
        post_json: dict = None,
        post_text: str = "",
        get_status: int = 200,
        get_json: dict = None,
        get_text: str = "",
    ):
        post_resp = mock_aiohttp_response(status=post_status, json_data=post_json, text=post_text)
        get_resp = mock_aiohttp_response(status=get_status, json_data=get_json, text=get_text)

        session = MagicMock()
        # session.post() returns a context manager, NOT a coroutine — use MagicMock, not AsyncMock
        session.post = MagicMock(return_value=post_resp)
        session.get = MagicMock(return_value=get_resp)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        return session

    return _make_session
