#!/usr/bin/env python
"""Сгенерировать валидный Telegram initData для локальной разработки Mini App.

Использование:
    python scripts/gen_dev_token.py

Создаёт/обновляет miniapp/.env с VITE_DEV_TOKEN и VITE_API_URL.
Токен действителен 1 час (ограничение API validate_init_data).
"""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

# Bot token — читаем из корневого .env
def load_env(path: str) -> dict:
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip("\"'")
    return env

root_env = load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))
bot_token = root_env.get("BOT_TOKEN")
if not bot_token:
    print("❌ BOT_TOKEN not found in .env")
    exit(1)

# Simulated Telegram user
user = {
    "id": 123456789,
    "first_name": "Dev",
    "last_name": "User",
    "username": "dev_user",
    "language_code": "en",
    "is_premium": False,
    "allows_write_to_pm": True,
}

auth_date = int(time.time())

# Build data_check_string (sorted params)
params = {
    "auth_date": str(auth_date),
    "user": json.dumps(user, separators=(",", ":")),
}
data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

# Compute HMAC
secret_key = hmac.new(
    b"WebAppData",
    bot_token.encode(),
    hashlib.sha256,
).digest()

hash_value = hmac.new(
    secret_key,
    data_check_string.encode(),
    hashlib.sha256,
).hexdigest()

# Build final initData
init_data = urlencode({
    "auth_date": str(auth_date),
    "user": json.dumps(user, separators=(",", ":")),
    "hash": hash_value,
})

# Write/update miniapp/.env
miniapp_env = os.path.join(os.path.dirname(__file__), "..", "miniapp", ".env")
env_content = f"""# Telegram Mini App initData for local development (regenerated: {time.strftime('%Y-%m-%d %H:%M:%S')})
# Внимание: токен действителен ~1 час (auth_date check в API).
# Запустите python scripts/gen_dev_token.py для обновления.
VITE_DEV_TOKEN={init_data}

# API URL для локальной разработки
VITE_API_URL=http://localhost:8000
"""

with open(miniapp_env, "w") as f:
    f.write(env_content)

print(f"✅ VITE_DEV_TOKEN generated (expires: {time.strftime('%H:%M:%S', time.localtime(auth_date + 3600))})")
print(f"   Written to {miniapp_env}")
