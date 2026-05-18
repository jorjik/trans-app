"""
Хранилище пользовательских настроек.
MVP: in-memory dict + опциональный Redis.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    telegram_id: int
    target_language: str = "en"
    source_language: str = "auto"
    favorite_langs: list[str] = field(default_factory=lambda: ["en", "de", "fr"])
    chars_used: int = 0
    chars_limit: int = 50_000
    plan: str = "free"

    @property
    def chars_remaining(self) -> int:
        return max(0, self.chars_limit - self.chars_used)

    @property
    def is_quota_exceeded(self) -> bool:
        return self.chars_used >= self.chars_limit

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# In-memory хранилище
_store: dict[int, UserSettings] = {}


def get_user(telegram_id: int) -> UserSettings:
    """Возвращает настройки пользователя. Создаёт если не существует."""
    if telegram_id not in _store:
        _store[telegram_id] = UserSettings(telegram_id=telegram_id)
    return _store[telegram_id]


def save_user(settings: UserSettings) -> None:
    _store[settings.telegram_id] = settings


def set_target_language(telegram_id: int, lang: str) -> UserSettings:
    user = get_user(telegram_id)
    user.target_language = lang
    # Добавляем в избранное если ещё нет
    if lang not in user.favorite_langs:
        user.favorite_langs.insert(0, lang)
        user.favorite_langs = user.favorite_langs[:5]  # max 5
    save_user(user)
    return user


def deduct_chars(telegram_id: int, count: int) -> UserSettings:
    user = get_user(telegram_id)
    user.chars_used += count
    save_user(user)
    return user


def add_chars(telegram_id: int, count: int) -> UserSettings:
    """Пополнение баланса (рефералы, апгрейд)."""
    user = get_user(telegram_id)
    user.chars_limit += count
    save_user(user)
    return user


def upgrade_plan(telegram_id: int, plan: str) -> UserSettings:
    """Активирует платный тариф после оплаты Stars."""
    from services.billing import PLAN_LIMITS

    if plan not in PLAN_LIMITS:
        raise ValueError(f"Unknown plan: {plan}")

    user = get_user(telegram_id)
    user.plan = plan
    user.chars_limit = PLAN_LIMITS[plan]
    user.chars_used = 0
    save_user(user)
    return user


def get_all_users_count() -> int:
    return len(_store)
