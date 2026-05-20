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
