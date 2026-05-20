"""
Security utilities:
- Telegram initData HMAC validation (для Mini App)
- JWT generation/verification
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, unquote

from jose import JWTError, jwt

from core.config import settings


# ── Telegram initData validation ───────────────────────────────────────────────

class InitDataError(Exception):
    pass


def validate_init_data(init_data: str) -> dict:
    """
    Валидирует initData от Telegram WebApp.
    Возвращает dict с данными пользователя или выбрасывает InitDataError.

    Алгоритм по официальной документации Telegram:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise InitDataError("Cannot parse init_data")

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise InitDataError("Missing hash in init_data")

    # Проверяем свежесть (не старше 1 часа)
    auth_date = params.get("auth_date")
    if auth_date:
        try:
            age = int(time.time()) - int(auth_date)
            if age > 3600:
                raise InitDataError("init_data expired")
        except ValueError:
            raise InitDataError("Invalid auth_date")

    # Строим data-check-string
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    # Вычисляем HMAC
    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataError("Invalid hash")

    # Декодируем user JSON
    user_raw = params.get("user")
    if not user_raw:
        raise InitDataError("No user in init_data")

    try:
        user = json.loads(unquote(user_raw))
    except json.JSONDecodeError:
        raise InitDataError("Cannot parse user JSON")

    return user


# ── JWT ────────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, telegram_id: int) -> str:
    """Создаёт JWT токен для пользователя."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "tg_id": telegram_id,
        "iat": now,
        "exp": now + settings.jwt_expire_seconds,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """
    Декодирует JWT токен.
    Возвращает payload или выбрасывает JWTError.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


# ── Telegram webhook secret ────────────────────────────────────────────────────

def validate_webhook_secret(secret: Optional[str]) -> bool:
    """Проверяет секрет webhook от Telegram."""
    if not settings.bot_webhook_secret:
        if settings.env != "development":
            return False
        return True  # секрет не настроен — пропускаем только в dev
    if not secret:
        return False
    return hmac.compare_digest(secret, settings.bot_webhook_secret)


# ── User ID hashing ────────────────────────────────────────────────────────────

def hash_telegram_id(telegram_id: int) -> str:
    """SHA-256 хэш telegram_id для lookup в БД."""
    return hashlib.sha256(
        f"{telegram_id}:{settings.secret_key}".encode()
    ).hexdigest()
