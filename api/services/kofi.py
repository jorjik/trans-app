"""Ko-fi webhook parsing and verification."""

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional

log = logging.getLogger(__name__)

PAYMENT_CODE_RE = re.compile(r"\bKF-[A-Z0-9]{8,16}\b", re.IGNORECASE)
PAYMENT_TYPES = {"Donation", "Subscription", "Shop Order", "Commission"}


@dataclass(frozen=True)
class KofiWebhookPayment:
    provider_payment_id: str
    verification_token: str
    amount: str
    currency: str
    message: str
    payment_type: str
    raw_payload: dict[str, Any]


def normalize_amount(value: Any) -> str:
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid amount") from None
    if amount <= 0:
        raise ValueError("Invalid amount")
    return format(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def amount_for_plan(price_stars: int, amount_per_star: str | float) -> str:
    """Рассчитывает сумму к оплате: stars * amount_per_star."""
    try:
        mult = Decimal(str(amount_per_star).strip())
        stars = Decimal(int(price_stars))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid amount settings") from None
    if mult <= 0 or stars <= 0:
        raise ValueError("Invalid amount settings")
    return normalize_amount(stars * mult)


def extract_kofi_code(message: str) -> Optional[str]:
    """Извлекает код платежа KF-XXXXXXXX из сообщения."""
    match = PAYMENT_CODE_RE.search(message or "")
    return match.group(0).upper() if match else None


def parse_kofi_webhook_payload(payload: dict[str, Any] | str) -> KofiWebhookPayment:
    """Парсит и валидирует входящий вебхук от Ko-fi."""
    data = _unwrap_payload(payload)
    provider_payment_id = str(
        data.get("kofi_transaction_id") or data.get("message_id") or ""
    ).strip()
    verification_token = str(data.get("verification_token") or "").strip()
    payment_type = str(data.get("type") or "").strip()
    currency = str(data.get("currency") or "").strip().upper()
    message = str(data.get("message") or "")

    if not provider_payment_id or not verification_token or not payment_type or not currency:
        raise ValueError("Invalid Ko-fi payload: missing required fields")

    if payment_type not in PAYMENT_TYPES:
        raise ValueError(f"Unsupported Ko-fi payment type: {payment_type}")

    return KofiWebhookPayment(
        provider_payment_id=provider_payment_id,
        verification_token=verification_token,
        amount=normalize_amount(data.get("amount")),
        currency=currency,
        message=message,
        payment_type=payment_type,
        raw_payload=data,
    )


def _unwrap_payload(payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(payload, str):
        value = json.loads(payload)
    else:
        value = payload
    if not isinstance(value, dict):
        raise ValueError("Invalid Ko-fi payload")
    wrapped = value.get("data")
    if isinstance(wrapped, str):
        value = json.loads(wrapped)
    elif isinstance(wrapped, dict):
        value = wrapped
    if not isinstance(value, dict):
        raise ValueError("Invalid Ko-fi payload")
    return value
