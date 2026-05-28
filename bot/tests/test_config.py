"""
Tests for bot/config.py — settings, env modes, and LOCAL_BOT_TOKEN override.

Run: cd bot && python -m pytest tests/test_config.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from config import settings
from typing import Optional


class TestBotTokenOverride:
    """Tests for _override_bot_token_for_dev validator.

    Проверяет, что токен подменяется только при:
      - ENV != production
      - LOCAL_BOT_TOKEN задан
    """

    def _patch_and_validate(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env: str,
        local_token: Optional[str],
        main_token: str = "123456:ABC-main",
    ) -> str:
        """Helper: monkeypatch settings, run validator, return final bot_token."""
        monkeypatch.setattr(settings, "env", env)
        monkeypatch.setattr(settings, "local_bot_token", local_token)
        monkeypatch.setattr(settings, "bot_token", main_token)

        settings._override_bot_token_for_dev()
        return settings.bot_token

    def test_dev_mode_uses_local_token(self, monkeypatch):
        """ENV=development + LOCAL_BOT_TOKEN задан → используется LOCAL_BOT_TOKEN."""
        result = self._patch_and_validate(
            monkeypatch,
            env="development",
            local_token="789012:XYZ-local",
        )
        assert result == "789012:XYZ-local"

    def test_production_keeps_main_token(self, monkeypatch):
        """ENV=production + LOCAL_BOT_TOKEN задан → остаётся BOT_TOKEN."""
        result = self._patch_and_validate(
            monkeypatch,
            env="production",
            local_token="789012:XYZ-local",
            main_token="123456:ABC-main",
        )
        assert result == "123456:ABC-main"

    def test_dev_mode_no_local_token(self, monkeypatch):
        """ENV=development + LOCAL_BOT_TOKEN=None → остаётся BOT_TOKEN."""
        result = self._patch_and_validate(
            monkeypatch,
            env="development",
            local_token=None,
            main_token="123456:ABC-main",
        )
        assert result == "123456:ABC-main"

    def test_dev_mode_empty_local_token(self, monkeypatch):
        """ENV=development + LOCAL_BOT_TOKEN='' → остаётся BOT_TOKEN."""
        result = self._patch_and_validate(
            monkeypatch,
            env="development",
            local_token="",
            main_token="123456:ABC-main",
        )
        assert result == "123456:ABC-main"

    def test_staging_mode_uses_local_token(self, monkeypatch):
        """Любой ENV != production (staging, testing) — тоже подменяет."""
        result = self._patch_and_validate(
            monkeypatch,
            env="staging",
            local_token="789012:XYZ-local",
            main_token="123456:ABC-main",
        )
        assert result == "789012:XYZ-local"

    def test_override_does_not_affect_other_fields(self, monkeypatch):
        """После подмены другие поля Settings не меняются."""
        monkeypatch.setattr(settings, "env", "development")
        monkeypatch.setattr(settings, "local_bot_token", "789012:XYZ-local")
        monkeypatch.setattr(settings, "bot_token", "123456:ABC-main")

        original_api_url = settings.api_url
        original_mini_app_url = settings.mini_app_url

        settings._override_bot_token_for_dev()

        assert settings.api_url == original_api_url
        assert settings.mini_app_url == original_mini_app_url


class TestUpdateSettingsLocalFallback:
    """Tests for update_settings local fallback when API is unavailable.

    Проверяет, что ui_language сохраняется в in-memory кэше,
    даже если API-запрос не удался (например, при локальной разработке).
    """

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        """Mock settings.api_url and aiohttp session to avoid real HTTP connections."""
        from services.api_client import _cache
        _cache.clear()
        monkeypatch.setattr("config.settings.api_url", "http://localhost:1")

        # Мокаем aiohttp session: session.post() возвращает контекст-менеджер,
        # у которого __aenter__ кидает ClientError (симулируем недоступный API).
        import aiohttp

        async def _raise_on_aenter(*args, **kwargs):
            raise aiohttp.ClientError("Mock: connection refused")

        mock_cm = MagicMock()
        mock_cm.__aenter__ = _raise_on_aenter
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_cm)
        mock_session.closed = False
        monkeypatch.setattr("services.api_client._session", mock_session)

    @pytest.mark.asyncio
    async def test_local_fallback_updates_cache(self, monkeypatch):
        """
        Если API недоступен, но передан ui_language, кэш обновляется локально.
        Последующий get_user должен вернуть ui_language из кэша.
        """
        from services.api_client import (
            update_settings, get_user, _cache,
        )

        telegram_id = 999001

        # 1. Сначала создаём запись в кэше (через get_user, который создаст дефолт)
        user = await get_user(telegram_id)
        assert user.ui_language == ""  # дефолт

        # 2. Обновляем ui_language через update_settings
        # API по localhost:1 недоступен, должен сработать локальный fallback
        result = await update_settings(telegram_id, ui_language="ru")
        assert result is True  # True от локального fallback

        # 3. Проверяем, что кэш обновлён
        cached = _cache.get(telegram_id)
        assert cached is not None
        assert cached[1].ui_language == "ru"

        # 4. get_user должен вернуть актуальные данные из кэша
        user2 = await get_user(telegram_id)
        assert user2.ui_language == "ru"

    @pytest.mark.asyncio
    async def test_local_fallback_only_ui_language(self, monkeypatch):
        """
        Локальный fallback срабатывает ТОЛЬКО для ui_language,
        не для target_language или favorite_langs.
        """
        from services.api_client import update_settings, get_user, _cache

        _cache.clear()
        telegram_id = 999002

        user = await get_user(telegram_id)
        assert user.target_language == "en"

        # Обновляем target_language — API недоступен, fallback НЕ срабатывает
        result = await update_settings(telegram_id, target_language="de")
        assert result is False  # API недоступен, fallback не для target_language

        user2 = await get_user(telegram_id)
        assert user2.target_language == "en"  # остался прежним

    @pytest.mark.asyncio
    async def test_local_fallback_no_cache_entry(self, monkeypatch):
        """
        Если в кэше нет записи для пользователя, local fallback
        не создаёт новую запись (только обновляет существующую).
        """
        from services.api_client import (
            update_settings, _cache_invalidate, _cache,
        )

        _cache.clear()
        telegram_id = 999003

        # Нет записи в кэше
        result = await update_settings(telegram_id, ui_language="fr")
        assert result is False  # нет кэша — fallback не сработал

