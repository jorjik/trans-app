"""
Tests for billing.py — Telegram Stars payments and plan management.

Run: cd bot && python -m pytest tests/test_billing.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.billing import cb_upgrade_plan, on_pre_checkout, on_successful_payment
from services.billing import (
    build_payload, parse_payload, get_plan, BILLABLE_PLANS,
    start_checkout, send_stars_invoice, notify_api_stars_paid,
)
from conftest import make_message, make_callback, FakeUserData


class TestBuildPayload:
    """Tests for build_payload and parse_payload."""

    def test_build_payload_format(self):
        payload = build_payload("starter", 123)
        assert payload == "pay:starter:123"

    def test_parse_payload_valid(self):
        result = parse_payload("pay:starter:123")
        assert result is not None
        assert result[0] == "starter"
        assert result[1] == 123

    def test_parse_payload_invalid_prefix(self):
        result = parse_payload("invalid:starter:123")
        assert result is None

    def test_parse_payload_wrong_parts(self):
        result = parse_payload("pay:starter")
        assert result is None

    def test_parse_payload_non_int_user_id(self):
        result = parse_payload("pay:starter:abc")
        assert result is None

    def test_parse_payload_empty(self):
        result = parse_payload("")
        assert result is None


class TestGetPlan:
    """Tests for get_plan."""

    def test_get_plan_starter(self):
        plan = get_plan("starter")
        assert plan is not None
        assert plan.id == "starter"
        assert plan.chars_limit == 500_000
        assert plan.stars == 250

    def test_get_plan_pro(self):
        plan = get_plan("pro")
        assert plan is not None
        assert plan.chars_limit == 2_000_000
        assert plan.stars == 750

    def test_get_plan_business(self):
        plan = get_plan("business")
        assert plan is not None
        assert plan.chars_limit == 10_000_000
        assert plan.stars == 2500

    def test_get_plan_unknown(self):
        plan = get_plan("nonexistent")
        assert plan is None

    def test_get_plan_free(self):
        """Free plan is not billable."""
        plan = get_plan("free")
        assert plan is None

    def test_billable_plans_all_present(self):
        assert "starter" in BILLABLE_PLANS
        assert "pro" in BILLABLE_PLANS
        assert "business" in BILLABLE_PLANS


class TestNotifyApiStarsPaid:
    """Tests for notify_api_stars_paid."""

    @pytest.mark.asyncio
    async def test_notify_no_api_url(self, monkeypatch):
        monkeypatch.setattr("services.billing.settings.api_url", None)
        result = await notify_api_stars_paid(
            telegram_id=123, plan_id="starter",
            charge_id="charge_1", total_amount=250,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_notify_success(self, monkeypatch):
        monkeypatch.setattr("services.billing.settings.api_url", "http://test-api")
        monkeypatch.setattr("services.billing.settings.bot_webhook_secret", "secret")

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("services.billing.aiohttp.ClientSession", return_value=mock_session):
            result = await notify_api_stars_paid(
                telegram_id=123, plan_id="starter",
                charge_id="charge_1", total_amount=250,
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_notify_api_error(self, monkeypatch):
        monkeypatch.setattr("services.billing.settings.api_url", "http://test-api")
        monkeypatch.setattr("services.billing.settings.bot_webhook_secret", "secret")

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("services.billing.aiohttp.ClientSession", return_value=mock_session):
            result = await notify_api_stars_paid(
                telegram_id=123, plan_id="starter",
                charge_id="charge_1", total_amount=250,
            )
            assert result is False


class TestStartCheckout:
    """Tests for start_checkout and send_stars_invoice."""

    @pytest.mark.asyncio
    async def test_start_checkout_unknown_plan(self, monkeypatch):
        msg = make_message("/start pay_starter", from_id=123)
        msg.text = "/start pay_starter"

        await start_checkout(msg, "nonexistent")

        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_stars_invoice(self, monkeypatch, patch_settings):
        mock_bot = AsyncMock()
        mock_bot.send_invoice = AsyncMock()
        mock_bot.send_invoice.return_value = MagicMock()

        await send_stars_invoice(mock_bot, 123, 456, "starter")

        mock_bot.send_invoice.assert_called_once()
        args = mock_bot.send_invoice.call_args[1]
        assert args["chat_id"] == 123
        assert args["currency"] == "XTR"
        assert "Starter" in args["title"]


class TestCbUpgradePlan:
    """Tests for cb_upgrade_plan handler."""

    @pytest.mark.asyncio
    async def test_cb_upgrade_invalid_plan(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="ru")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        cb = make_callback("upgrade:nonexistent", from_id=123)
        await cb_upgrade_plan(cb)

        cb.answer.assert_called_once()
        cb.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cb_upgrade_starter(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        mock_bot = AsyncMock()
        mock_bot.send_invoice = AsyncMock()

        cb = make_callback("upgrade:starter", from_id=123)
        cb.bot = mock_bot
        cb.message.bot = mock_bot

        await cb_upgrade_plan(cb)

        cb.answer.assert_called_once()


class TestOnPreCheckout:
    """Tests for on_pre_checkout handler."""

    @pytest.mark.asyncio
    async def test_pre_checkout_valid(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        query = MagicMock(answer=AsyncMock())
        query.from_user.id = 123
        query.invoice_payload = "pay:starter:123"
        query.currency = "XTR"
        query.total_amount = 250

        await on_pre_checkout(query)

        query.answer.assert_called_once_with(ok=True)

    @pytest.mark.asyncio
    async def test_pre_checkout_wrong_user(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        query = MagicMock(answer=AsyncMock())
        query.from_user.id = 999
        query.invoice_payload = "pay:starter:123"
        query.currency = "XTR"
        query.total_amount = 250

        await on_pre_checkout(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1]["ok"] is False

    @pytest.mark.asyncio
    async def test_pre_checkout_wrong_amount(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        query = MagicMock(answer=AsyncMock())
        query.from_user.id = 123
        query.invoice_payload = "pay:starter:123"
        query.currency = "XTR"
        query.total_amount = 100  # wrong amount

        await on_pre_checkout(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1]["ok"] is False

    @pytest.mark.asyncio
    async def test_pre_checkout_invalid_payload(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        query = MagicMock(answer=AsyncMock())
        query.from_user.id = 123
        query.invoice_payload = "invalid"

        await on_pre_checkout(query)

        query.answer.assert_called_once()
        assert query.answer.call_args[1]["ok"] is False


class TestOnSuccessfulPayment:
    """Tests for on_successful_payment handler."""

    @pytest.mark.asyncio
    async def test_successful_payment(self, monkeypatch, patch_settings):
        mock_upgrade = AsyncMock(return_value=True)
        mock_notify = AsyncMock(return_value=True)
        monkeypatch.setattr("handlers.billing.upgrade_plan", mock_upgrade)
        monkeypatch.setattr("handlers.billing.notify_api_stars_paid", mock_notify)

        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en", plan="starter", chars_limit=500000)
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        msg = make_message("payment success", from_id=123)
        msg.successful_payment = MagicMock()
        msg.successful_payment.invoice_payload = "pay:starter:123"
        msg.successful_payment.telegram_payment_charge_id = "charge_1"
        msg.successful_payment.total_amount = 250

        await on_successful_payment(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Starter" in call_text or "500" in call_text

    @pytest.mark.asyncio
    async def test_successful_payment_invalid_payload(self, monkeypatch, patch_settings):
        async def fake_get_user(tg_id):
            return FakeUserData(telegram_id=123, ui_language="en")
        monkeypatch.setattr("handlers.billing.get_user", fake_get_user)

        msg = make_message("payment success", from_id=123)
        msg.successful_payment = MagicMock()
        msg.successful_payment.invoice_payload = "invalid"

        await on_successful_payment(msg)

        msg.answer.assert_called_once()
