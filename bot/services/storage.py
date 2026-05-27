"""
Хранилище пользовательских настроек.
Persistent: использует Backend API через api_client.
In-memory: с TTL-кэшем для быстрого доступа.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.api_client import (
    UserData,
    get_user as _api_get_user,
    deduct_chars as _api_deduct_chars,
    update_settings as _api_update_settings,
    upgrade_plan as _api_upgrade_plan,
    _api_get_group_config,
    _api_update_group_config,
)

logger = logging.getLogger(__name__)


# ── Public API (совместимость с существующими обработчиками) ──────────────────


async def get_user(telegram_id: int) -> UserData:
    """Возвращает данные пользователя из API (с in-memory кэшем)."""
    return await _api_get_user(telegram_id)


async def deduct_chars(telegram_id: int, count: int) -> Optional[UserData]:
    """Списывает символы через API."""
    return await _api_deduct_chars(telegram_id, count)


async def set_target_language(telegram_id: int, lang: str) -> UserData:
    """Устанавливает язык перевода."""
    await _api_update_settings(telegram_id, target_language=lang)
    return await _api_get_user(telegram_id)


async def upgrade_plan(telegram_id: int, plan: str) -> bool:
    """Активирует платный тариф."""
    return await _api_upgrade_plan(telegram_id, plan)


async def sync_ui_language(telegram_id: int, ui_language: str) -> bool:
    """Синхронизирует язык интерфейса."""
    return await _api_update_settings(telegram_id, ui_language=ui_language)


# ── Group config (автоперевод в группах) ──────────────────────

async def get_group_config(chat_id: int) -> dict | None:
    """Получает настройки группового перевода из API."""
    return await _api_get_group_config(chat_id)


async def update_group_config(
    chat_id: int,
    chat_title: str | None = None,
    target_lang: str | None = None,
    is_active: bool | None = None,
    translator_uid: int | None = None,
) -> bool:
    """Создаёт или обновляет настройки группового перевода."""
    return await _api_update_group_config(
        chat_id=chat_id,
        chat_title=chat_title,
        target_lang=target_lang,
        is_active=is_active,
        translator_uid=translator_uid,
    )
