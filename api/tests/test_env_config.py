"""Tests: validate that all required .env variables are set.

Run: cd api && python -m pytest tests/test_env_config.py -v

Categories:
  [REQUIRED]  — must be set, app won't work without them
  [PAYMENT]   — needed if that payment method should work
  [PRODUCTION]— warnings in production mode only
"""

import os
import sys
from pathlib import Path

# Ensure we can import from api/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

# ── Constants ─────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # trans-app/
DOTENV_PATH = PROJECT_ROOT / ".env"

PLACEHOLDER_SECRET_KEY = "change-me-in-production-min-64-chars"
PLACEHOLDER_INTERNAL_SECRET = "change-me-bot-secret"

# Required variables (app won't work without them)
CORE_REQUIRED = [
    ("BOT_TOKEN", "Telegram bot token"),
    ("DATABASE_URL", "PostgreSQL connection string"),
    ("SECRET_KEY", "JWT signing key (min 64 chars)"),
    ("BOT_INTERNAL_SECRET", "Secret for API ↔ bot auth"),
]

# Payment method groups (all-or-nothing per method)
PAYMENT_GROUPS: list[tuple[str, list[str], str]] = [
    (
        "Monobank",
        ["MONOBANK_TOKEN", "MONOBANK_WEBHOOK_URL"],
        "MONOBANK_TOKEN is set — MONOBANK_WEBHOOK_URL should also be configured",
    ),
    (
        "Ko-fi",
        ["KOFI_VERIFICATION_TOKEN", "KOFI_PAGE_URL"],
        "KOFI_VERIFICATION_TOKEN is set — KOFI_PAGE_URL should also be configured",
    ),
    (
        "PayPal",
        ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
        "PAYPAL_CLIENT_ID is set — PAYPAL_CLIENT_SECRET should also be configured",
    ),
]

# Variables that should NOT be placeholders in production
PLACEHOLDER_CHECKS = [
    ("SECRET_KEY", PLACEHOLDER_SECRET_KEY, "SECRET_KEY is still the placeholder"),
    ("BOT_INTERNAL_SECRET", PLACEHOLDER_INTERNAL_SECRET, "BOT_INTERNAL_SECRET is still the placeholder"),
]

# Optional but commonly expected
OPTIONAL_KNOWN = [
    "REDIS_URL",
    "ENV",
    "DEBUG",
    "LOG_LEVEL",
    "CORS_ORIGINS",
    "BOT_WEBHOOK_SECRET",
    "MINI_APP_URL",
    "BACKEND_API_URL",
    "ADMIN_TG_IDS",
    "FREE_PLAN_CHARS",
    "REFERRAL_BONUS_CHARS",
    "CACHE_TTL_SHORT",
    "CACHE_TTL_LONG",
    "DEEPL_API_KEY",
    "GOOGLE_TRANSLATE_API_KEY",
    "OPENAI_API_KEY",
    "DEFAULT_TRANSLATION_ENGINE",
    "MONOBANK_CURRENCY",
    "MONOBANK_AMOUNT_PER_STAR",
    "KOFI_CURRENCY",
    "KOFI_AMOUNT_PER_STAR",
    "PAYPAL_MODE",
    "PAYPAL_CURRENCY",
    "PAYPAL_AMOUNT_PER_STAR",
    "DATABASE_POOL_SIZE",
    "DATABASE_MAX_OVERFLOW",
]


# ── Helpers ───────────────────────────────────────────────────────────────────


def load_dotenv() -> dict[str, str]:
    """Parse .env file and return {KEY: VALUE} dict. Skips comments and blank lines."""
    if not DOTENV_PATH.exists():
        return {}

    env: dict[str, str] = {}
    with open(DOTENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def dotenv_vars() -> dict[str, str]:
    """Load .env once per test session."""
    return load_dotenv()


@pytest.fixture
def mock_production_env(monkeypatch):
    """Set ENV=production as if running in production."""
    monkeypatch.setenv("ENV", "production")
    # Reload settings to pick up the override
    from core.config import settings
    monkeypatch.setattr(settings, "env", "production")


# ── Tests: .env file exists ───────────────────────────────────────────────────


class TestDotenvFile:
    """Basic checks: .env file is present and parseable."""

    def test_dotenv_exists(self):
        assert DOTENV_PATH.exists(), (
            f".env not found at {DOTENV_PATH}\n"
            "  Create it from .env.example (see docs/DEPLOY-COOLIFY.md for production)"
        )

    def test_dotenv_not_empty(self, dotenv_vars):
        assert len(dotenv_vars) > 0, (
            ".env is empty or unparseable\n"
            "  Expected format: KEY=VALUE (one per line)"
        )

    def test_dotenv_no_duplicates(self):
        """Ensure no duplicate keys (last wins in bash, but it's error-prone)."""
        keys_seen: set[str] = set()
        duplicates: list[str] = []
        with open(DOTENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.partition("=")[0].strip()
                if key in keys_seen:
                    duplicates.append(key)
                keys_seen.add(key)
        assert not duplicates, f"Duplicate keys in .env: {duplicates}"


# ── Tests: core required vars ────────────────────────────────────────────────


class TestCoreRequired:
    """Variables without which the app won't start or function."""

    @pytest.mark.parametrize("var,description", CORE_REQUIRED)
    def test_core_var_set(self, dotenv_vars, var, description):
        value = dotenv_vars.get(var, "")
        assert value, (
            f"[REQUIRED] {var} is not set in .env ({description})\n"
            f"  Add it: echo '{var}=your_value' >> {DOTENV_PATH}"
        )

    @pytest.mark.parametrize("var,placeholder,msg", PLACEHOLDER_CHECKS)
    def test_core_var_not_placeholder(self, dotenv_vars, var, placeholder, msg):
        value = dotenv_vars.get(var, "")
        if value == placeholder:
            pytest.fail(
                f"[WARNING] {msg}\n"
                f"  Current value: '{value}'\n"
                f"  Generate a strong random value and update .env"
            )

    def test_secret_key_min_length(self, dotenv_vars):
        """SECRET_KEY should be at least 32 chars (64 recommended)."""
        value = dotenv_vars.get("SECRET_KEY", "")
        if value and value not in (PLACEHOLDER_SECRET_KEY, ""):
            assert len(value) >= 32, (
                f"[WARNING] SECRET_KEY is too short ({len(value)} chars, min 32 recommended)\n"
                f"  Current value ends with: '...{value[-8:]}'"
            )


# ── Tests: payment method vars ────────────────────────────────────────────────


class TestPaymentConfig:
    """Payment methods: warn when partially configured."""

    @pytest.mark.parametrize("name,vars_to_check,hint", PAYMENT_GROUPS)
    def test_payment_group_completeness(self, dotenv_vars, name, vars_to_check, hint):
        set_values = {v: dotenv_vars.get(v, "") for v in vars_to_check}
        set_count = sum(1 for v in set_values.values() if v)

        if set_count == 0:
            pytest.skip(f"{name}: not configured (all vars empty)")
        elif set_count < len(vars_to_check):
            missing = [v for v, val in set_values.items() if not val]
            pytest.fail(
                f"[PAYMENT] {name}: incomplete configuration\n"
                f"  Missing: {', '.join(missing)}\n"
                f"  Hint: {hint}"
            )

    def test_monobank_webhook_url_consistency(self, dotenv_vars):
        """If MONOBANK_TOKEN is set, check that webhook URL looks valid."""
        token = dotenv_vars.get("MONOBANK_TOKEN", "")
        webhook = dotenv_vars.get("MONOBANK_WEBHOOK_URL", "")
        if not token:
            pytest.skip("Monobank not configured")
        if webhook:
            assert webhook.startswith("https://"), (
                "[PAYMENT] MONOBANK_WEBHOOK_URL should start with https://\n"
                f"  Current: {webhook}"
            )


# ── Tests: production mode ────────────────────────────────────────────────────


class TestProductionConfig:
    """Extra checks that run only when ENV=production."""

    @pytest.mark.parametrize("var,placeholder,msg", PLACEHOLDER_CHECKS)
    def test_production_no_placeholders(self, dotenv_vars, mock_production_env, var, placeholder, msg):
        value = dotenv_vars.get(var, "")
        assert value != placeholder, (
            f"[PRODUCTION] {msg}\n"
            f"  This is a security risk in production!"
        )
        assert value, (
            f"[PRODUCTION] {var} is empty — it must be set in production!"
        )

    def test_production_webhook_secret(self, dotenv_vars, mock_production_env):
        value = dotenv_vars.get("BOT_WEBHOOK_SECRET", "")
        assert value, (
            "[PRODUCTION] BOT_WEBHOOK_SECRET is not set — Telegram webhook won't be secure"
        )

    def test_production_env_var(self, dotenv_vars):
        env_val = dotenv_vars.get("ENV", "")
        if env_val == "production":
            assert dotenv_vars.get("LOG_LEVEL", "") in ("INFO", "WARNING", "ERROR"), (
                "[PRODUCTION] LOG_LEVEL should be INFO, WARNING, or ERROR (not DEBUG)"
            )


# ── Inventory: show what's set vs what's known ────────────────────────────────


class TestEnvInventory:
    """Report variables that are set but unknown (possible typos)."""

    def test_unknown_vars_report(self, dotenv_vars):
        """List variables that are not in any known category (possible typos)."""
        all_known = {var for var, _ in CORE_REQUIRED}
        all_known.update(OPTIONAL_KNOWN)

        # Include payment group vars
        for _, vars_list, _ in PAYMENT_GROUPS:
            all_known.update(vars_list)

        set_vars = set(dotenv_vars.keys())
        unknown = set_vars - all_known

        # Filter out common shell env vars that leak in
        known_extra = {"host", "login", "password", "ADMIN_CHAT_ID",
                       "TELEGRAM_ID_ENCRYPTION_KEY", "TELEGRAM_PAYMENT_TOKEN",
                       "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
                       "YOOKASSA_SHOP_ID", "YOOKASSA_SECRET_KEY"}
        unknown -= known_extra

        if unknown:
            pytest.skip(
                f"Unknown variables in .env (possibly typos or legacy):\n"
                f"  {', '.join(sorted(unknown))}\n"
                f"  Remove if unused."
            )

    def test_optional_vars_coverage(self, dotenv_vars):
        """Show which optional vars are set for situational awareness."""
        set_opts = [v for v in OPTIONAL_KNOWN if dotenv_vars.get(v)]
        not_set = [v for v in OPTIONAL_KNOWN if not dotenv_vars.get(v)]

        sections = []
        if set_opts:
            sections.append(f"  Set ({len(set_opts)}): {', '.join(sorted(set_opts))}")
        if not_set:
            sections.append(f"  Not set ({len(not_set)}): {', '.join(sorted(not_set))}")

        msg = "Optional variables overview:\n" + "\n".join(sections)
        pytest.skip(msg)  # Informational — not a failure
