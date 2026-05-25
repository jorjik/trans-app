"""Tests for api/services/monobank.py — Monobank Acquiring API client.

Run: cd api && python -m pytest tests/test_monobank.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


# ── Helpers: _amount_to_kopiykas ──────────────────────────────────────────────

class TestAmountToKopiykas:
    """Tests for the _amount_to_kopiykas helper function."""

    def test_whole_uah(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("12") == 1200

    def test_with_decimals(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("12.34") == 1234

    def test_one_decimal_digit(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("12.3") == 1230

    def test_zero(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("0") == 0

    def test_zero_with_decimals(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("0.00") == 0

    def test_five_uah(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("5.00") == 500

    def test_large_amount(self):
        from services.monobank import _amount_to_kopiykas
        assert _amount_to_kopiykas("9999.99") == 999999


class TestAmountForPlan:
    """Tests for the amount_for_plan helper function."""

    def test_starter_with_str(self):
        from services.monobank import amount_for_plan
        assert amount_for_plan(250, "0.02") == "5.00"

    def test_pro_with_float(self):
        from services.monobank import amount_for_plan
        assert amount_for_plan(750, 0.02) == "15.00"

    def test_business(self):
        from services.monobank import amount_for_plan
        assert amount_for_plan(2500, 0.02) == "50.00"

    def test_custom_rate(self):
        from services.monobank import amount_for_plan
        assert amount_for_plan(250, "0.05") == "12.50"

    def test_zero_stars(self):
        from services.monobank import amount_for_plan
        assert amount_for_plan(0, 0.02) == "0.00"


# ── MonobankClient: create_invoice ────────────────────────────────────────────

class TestMonobankClientCreateInvoice:
    """Tests for MonobankClient.create_invoice."""

    @pytest.mark.asyncio
    async def test_success(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            post_status=200,
            post_json={
                "invoiceId": "test_invoice_123",
                "pageUrl": "https://pay.monobank.ua/test_invoice_123",
            }
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.create_invoice(
            amount="15.00",
            reference="user_1_plan_pro",
            destination="TransApp Pro",
            redirect_url="https://t.me/transapp_bot",
            webhook_url="https://test.api/webhook/monobank",
        )

        assert result is not None
        assert result["invoiceId"] == "test_invoice_123"
        assert result["pageUrl"] == "https://pay.monobank.ua/test_invoice_123"
        assert client.last_error is None
        mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token(self, monkeypatch):
        monkeypatch.setattr("core.config.settings.monobank_token", "")

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.create_invoice(
            amount="15.00",
            reference="user_1",
            destination="Test",
            redirect_url="https://t.me/bot",
            webhook_url="https://test.api/webhook/monobank",
        )

        assert result is None
        assert client.last_error == "token_missing"

    @pytest.mark.asyncio
    async def test_api_error_4xx(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            post_status=400,
            post_text="Bad request",
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.create_invoice(
            amount="15.00",
            reference="user_1",
            destination="Test",
            redirect_url="https://t.me/bot",
            webhook_url="https://test.api/webhook/monobank",
        )

        assert result is None
        assert client.last_error == "mono_400"

    @pytest.mark.asyncio
    async def test_api_error_500(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            post_status=500,
            post_text="Internal Server Error",
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.create_invoice(
            amount="15.00",
            reference="user_1",
            destination="Test",
            redirect_url="https://t.me/bot",
            webhook_url="https://test.api/webhook/monobank",
        )

        assert result is None
        assert client.last_error == "mono_500"

    @pytest.mark.asyncio
    async def test_transport_error(self, mocker):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=TimeoutError("Connection timed out"))
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.create_invoice(
            amount="15.00",
            reference="user_1",
            destination="Test",
            redirect_url="https://t.me/bot",
            webhook_url="https://test.api/webhook/monobank",
        )

        assert result is None
        assert "transport_error" in (client.last_error or "")


# ── MonobankClient: get_invoice_status ────────────────────────────────────────

class TestMonobankClientGetStatus:
    """Tests for MonobankClient.get_invoice_status."""

    @pytest.mark.asyncio
    async def test_success(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            get_status=200,
            get_json={
                "invoiceId": "test_123",
                "status": "success",
                "amount": 1500,
            }
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.get_invoice_status("test_123")

        assert result is not None
        assert result["status"] == "success"
        assert result["invoiceId"] == "test_123"
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token(self, monkeypatch):
        monkeypatch.setattr("core.config.settings.monobank_token", "")

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.get_invoice_status("test_123")

        assert result is None
        assert client.last_error == "token_missing"

    @pytest.mark.asyncio
    async def test_api_error(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            get_status=404,
            get_text="Not found",
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.get_invoice_status("test_123")

        assert result is None
        assert client.last_error == "mono_404"


# ── MonobankClient: cancel_invoice ────────────────────────────────────────────

class TestMonobankClientCancel:
    """Tests for MonobankClient.cancel_invoice."""

    @pytest.mark.asyncio
    async def test_success(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            post_status=200,
            post_json={"status": "canceled", "invoiceId": "test_123"},
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.cancel_invoice("test_123")

        assert result is not None
        assert result["status"] == "canceled"
        mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token(self, monkeypatch):
        monkeypatch.setattr("core.config.settings.monobank_token", "")

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.cancel_invoice("test_123")

        assert result is None
        assert client.last_error == "token_missing"

    @pytest.mark.asyncio
    async def test_api_error(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            post_status=403,
            post_text="Forbidden",
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import MonobankClient
        client = MonobankClient()
        result = await client.cancel_invoice("test_123")

        assert result is None
        assert client.last_error == "mono_403"


# ── fetch_public_key ──────────────────────────────────────────────────────────

class TestFetchPublicKey:
    """Tests for the fetch_public_key function."""

    @pytest.mark.asyncio
    async def test_success(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            get_status=200,
            get_json={"key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"},
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import fetch_public_key
        result = await fetch_public_key()

        assert result is not None
        assert "BEGIN PUBLIC KEY" in result

    @pytest.mark.asyncio
    async def test_no_token(self, monkeypatch):
        monkeypatch.setattr("core.config.settings.monobank_token", "")

        from services.monobank import fetch_public_key
        result = await fetch_public_key()

        assert result is None

    @pytest.mark.asyncio
    async def test_api_error(self, mocker, mock_aiohttp_session):
        mock_session = mock_aiohttp_session(
            get_status=500,
            get_text="Error",
        )
        mocker.patch("aiohttp.ClientSession", return_value=mock_session)

        from services.monobank import fetch_public_key
        result = await fetch_public_key()

        assert result is None


# ── verify_webhook_signature ──────────────────────────────────────────────────

class TestVerifyWebhookSignature:
    """Tests for the verify_webhook_signature function."""

    def test_valid_signature(self, mocker):
        mock_vk = MagicMock()
        mock_vk.verify = MagicMock(return_value=True)

        mocker.patch("ecdsa.VerifyingKey.from_pem", return_value=mock_vk)
        mocker.patch("ecdsa.util.sigdecode_der")

        from services.monobank import verify_webhook_signature

        result = verify_webhook_signature(
            b'{"test": "data"}',
            "dGVzdF9zaWc=",
            "-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----",
        )
        assert result is True
        mock_vk.verify.assert_called_once()

    def test_invalid_signature(self, mocker):
        mock_vk = MagicMock()
        mock_vk.verify = MagicMock(side_effect=Exception("Bad signature"))

        mocker.patch("ecdsa.VerifyingKey.from_pem", return_value=mock_vk)
        mocker.patch("ecdsa.util.sigdecode_der")

        from services.monobank import verify_webhook_signature

        result = verify_webhook_signature(
            b'{"test": "data"}',
            "dGVzdF9zaWc=",
            "-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----",
        )
        assert result is False

    def test_no_ecdsa_library(self, mocker):
        """When ecdsa is not installed, verification is skipped (returns True)."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "ecdsa":
                raise ImportError("No module named 'ecdsa'")
            return original_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", mock_import)

        from services.monobank import verify_webhook_signature

        result = verify_webhook_signature(b"test", "dGVzdA==", "key")
        assert result is True  # Skip verification when library missing

    def test_bad_base64(self, mocker):
        mocker.patch("ecdsa.VerifyingKey.from_pem", return_value=MagicMock())

        from services.monobank import verify_webhook_signature

        result = verify_webhook_signature(b"test", "!!!invalid-base64!!!", "key")
        assert result is False

    def test_bad_pem_key(self, mocker):
        mocker.patch("ecdsa.VerifyingKey.from_pem", side_effect=Exception("Invalid PEM"))

        from services.monobank import verify_webhook_signature

        result = verify_webhook_signature(b"test", "dGVzdA==", "not-a-pem-key")
        assert result is False
