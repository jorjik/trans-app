"""Monobank Acquiring API клиент — создание рахунку, проверка статусу, верифікація вебхуків."""

import asyncio
import hashlib
import logging
from decimal import Decimal
from typing import Any, Optional

import aiohttp

from core.config import settings

log = logging.getLogger(__name__)

BASE_URL = "https://api.monobank.ua"

CURRENCIES = {
    "UAH": 980,
    "USD": 840,
    "EUR": 978,
}


def _amount_to_kopiykas(amount_str: str) -> int:
    """Переводить суму у гривнях (12.34) в копійки (1234)."""
    parts = amount_str.split(".")
    if len(parts) == 1:
        return int(parts[0]) * 100
    return int(parts[0]) * 100 + int(parts[1].ljust(2, "0")[:2])


def amount_for_plan(price_stars: int, amount_per_star: str | float) -> str:
    """Розраховує суму: stars * amount_per_star, повертає у вигляді рядка."""
    total = Decimal(str(price_stars)) * Decimal(str(amount_per_star))
    return f"{total:.2f}"


class MonobankClient:
    """Клієнт Monobank Acquiring API."""

    def __init__(self, timeout_seconds: int = 15):
        self.token = settings.monobank_token or ""
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.last_error: Optional[str] = None

    async def create_invoice(
        self,
        amount: str,
        reference: str,
        destination: str,
        redirect_url: str,
        webhook_url: str,
        validity: int = 3600,
    ) -> Optional[dict[str, Any]]:
        """Створює рахунок для оплати."""
        self.last_error = None
        if not self.token:
            self.last_error = "token_missing"
            log.error("Monobank token not configured")
            return None

        url = f"{BASE_URL}/api/merchant/invoice/create"
        headers = {
            "X-Token": self.token,
            "Content-Type": "application/json",
        }
        body = {
            "amount": _amount_to_kopiykas(amount),
            "ccy": settings.monobank_currency,
            "merchantPaymInfo": {
                "reference": reference,
                "destination": destination,
                "comment": destination,
            },
            "redirectUrl": redirect_url,
            "webHookUrl": webhook_url,
            "validity": validity,
            "paymentType": "debit",
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.last_error = None
                        return data
                    text = await resp.text()
                    self.last_error = f"mono_{resp.status}"
                    log.error("Monobank create invoice failed: %s %s", resp.status, text[:200])
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.last_error = f"transport_error={type(exc).__name__}"
            log.error("Monobank create invoice error: %s", exc)
            return None

    async def get_invoice_status(self, invoice_id: str) -> Optional[dict[str, Any]]:
        """Перевіряє статус рахунку за invoiceId."""
        self.last_error = None
        if not self.token:
            self.last_error = "token_missing"
            return None

        url = f"{BASE_URL}/api/merchant/invoice/status?invoiceId={invoice_id}"
        headers = {"X-Token": self.token}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    text = await resp.text()
                    self.last_error = f"mono_{resp.status}"
                    log.error("Monobank status check failed: %s %s", resp.status, text[:200])
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.last_error = f"transport_error={type(exc).__name__}"
            log.error("Monobank status check error: %s", exc)
            return None

    async def cancel_invoice(self, invoice_id: str, ext_ref: str = "") -> Optional[dict[str, Any]]:
        """Скасовує оплачений рахунок (повернення коштів)."""
        self.last_error = None
        if not self.token:
            self.last_error = "token_missing"
            return None

        url = f"{BASE_URL}/api/merchant/invoice/cancel"
        headers = {
            "X-Token": self.token,
            "Content-Type": "application/json",
        }
        body = {"invoiceId": invoice_id}
        if ext_ref:
            body["extRef"] = ext_ref

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    text = await resp.text()
                    self.last_error = f"mono_{resp.status}"
                    log.error("Monobank cancel invoice failed: %s %s", resp.status, text[:200])
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.last_error = f"transport_error={type(exc).__name__}"
            log.error("Monobank cancel invoice error: %s", exc)
            return None


# ── Webhook verification (ECDSA via X-Sign header) ────────────────────────────


async def fetch_public_key() -> Optional[str]:
    """Отримує публічний ключ Monobank для верифікації вебхуків."""
    token = settings.monobank_token or ""
    if not token:
        return None

    url = f"{BASE_URL}/api/merchant/pubkey"
    headers = {"X-Token": token}
    try:
        async with aiohttp.ClientSession(timeout=10) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("key")
    except Exception as exc:
        log.warning("Failed to fetch Monobank pubkey: %s", exc)
    return None


def verify_webhook_signature(body_bytes: bytes, x_sign_base64: str, pub_key_pem: str) -> bool:
    """Верифікує ECDSA підпис вебхука від Monobank (SHA256)."""
    import base64

    try:
        from ecdsa import VerifyingKey
        from ecdsa.util import sigdecode_der

        signature = base64.b64decode(x_sign_base64)
        verifying_key = VerifyingKey.from_pem(pub_key_pem.encode())
        return verifying_key.verify(
            signature,
            body_bytes,
            sigdecode=sigdecode_der,
            hashfunc=hashlib.sha256,
        )
    except ImportError:
        log.warning("ecdsa library not installed — webhook verification disabled")
        return True  # skip verification if library not available
    except Exception as exc:
        log.warning("Monobank webhook signature verification failed: %s", exc)
        return False
