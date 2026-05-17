# API — Схема эндпоинтов и взаимодействие компонентов

---

## 1. Аутентификация

Все запросы от Mini App используют JWT-токен в заголовке:
```
Authorization: Bearer <jwt_token>
```

Токен получается через:

### POST /auth/telegram
Валидация initData из Telegram WebApp SDK.

**Request:**
```json
{
  "init_data": "query_id=...&user=...&auth_date=...&hash=..."
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 12345,
    "telegram_id_hash": "abc123",
    "target_language": "ru",
    "plan": "free",
    "chars_remaining": 48200
  }
}
```

**Response 401:**
```json
{ "error": "invalid_init_data", "message": "HMAC validation failed" }
```

---

## 2. Translation API

### POST /translate
Основной эндпоинт перевода (используется ботом и Mini App).

**Request:**
```json
{
  "text": "Hello, how are you?",
  "source_lang": "auto",
  "target_lang": "ru",
  "context": "chat",
  "engine": "auto"
}
```

**Response 200:**
```json
{
  "translated_text": "Привет, как дела?",
  "source_lang_detected": "en",
  "target_lang": "ru",
  "provider": "deepl",
  "cached": false,
  "char_count": 19,
  "chars_remaining": 48181
}
```

**Response 402 (лимит исчерпан):**
```json
{
  "error": "quota_exceeded",
  "message": "Monthly limit reached",
  "chars_used": 50000,
  "chars_limit": 50000,
  "reset_at": "2025-09-01T00:00:00Z",
  "upgrade_url": "https://t.me/transappbot?start=upgrade"
}
```

**Response 429 (rate limit):**
```json
{
  "error": "rate_limit",
  "retry_after": 1
}
```

---

## 3. Users API

### GET /users/me
```json
{
  "id": 12345,
  "target_language": "ru",
  "favorite_langs": ["en", "de", "fr"],
  "preferred_engine": "auto",
  "plan": "starter",
  "chars_limit": 500000,
  "chars_used": 123456,
  "chars_remaining": 376544,
  "reset_at": "2025-09-01T00:00:00Z",
  "created_at": "2025-07-15T10:00:00Z"
}
```

### PATCH /users/me
**Request:**
```json
{
  "target_language": "de",
  "favorite_langs": ["de", "en", "fr"],
  "preferred_engine": "deepl"
}
```

**Response 200:** обновлённый объект пользователя

---

## 4. Chats API (авто-переводы)

### GET /chats
```json
{
  "items": [
    {
      "id": 1,
      "chat_id": -1001234567890,
      "chat_title": "International Dev Chat",
      "chat_username": "devs_world",
      "source_lang": "auto",
      "target_lang": "ru",
      "is_active": true,
      "last_synced_at": "2025-08-20T10:30:00Z"
    }
  ],
  "total": 1,
  "limit_reached": false,
  "max_chats": 5
}
```

### POST /chats
**Request:**
```json
{
  "chat_username": "devs_world",
  "source_lang": "auto",
  "target_lang": "ru"
}
```

**Response 201:** созданный объект чата

**Response 403:**
```json
{ "error": "chat_limit_reached", "max_chats": 5 }
```

### GET /chats/{id}/messages
Получить последние N переведённых сообщений.

**Query params:** `limit=20&offset=0`

**Response 200:**
```json
{
  "items": [
    {
      "message_id": 9876,
      "date": "2025-08-20T10:25:00Z",
      "original_text": "Let me know if you need help",
      "translated_text": "Дайте знать, если нужна помощь",
      "source_lang": "en",
      "sender_name": "John"
    }
  ],
  "total": 47
}
```

### PATCH /chats/{id}
Изменить настройки или is_active.

### DELETE /chats/{id}
Удалить конфигурацию авто-перевода.

---

## 5. Stats API

### GET /stats/me
```json
{
  "period": "30d",
  "total_chars": 123456,
  "total_requests": 892,
  "chars_by_day": [
    { "date": "2025-08-01", "chars": 4200 },
    { "date": "2025-08-02", "chars": 3800 }
  ],
  "top_languages": [
    { "lang": "en", "chars": 89000 },
    { "lang": "de", "chars": 23000 }
  ],
  "providers_used": {
    "deepl": 78,
    "google": 14,
    "openai": 8
  }
}
```

---

## 6. Billing API

### GET /plans
```json
{
  "plans": [
    {
      "id": "free",
      "name": "Free",
      "chars_per_month": 50000,
      "price_usd": 0,
      "price_stars": 0,
      "price_usd_yearly": 0,
      "price_stars_yearly": 0,
      "max_auto_chats": 2,
      "features": ["basic_translate", "inline_mode"]
    },
    {
      "id": "starter",
      "name": "Starter",
      "chars_per_month": 500000,
      "price_usd": 2.5,
      "price_stars": 125,
      "price_usd_yearly": 18,
      "price_stars_yearly": 900,
      "max_auto_chats": 5,
      "features": ["basic_translate", "inline_mode", "auto_translate", "stats"]
    },
    {
      "id": "pro",
      "name": "Pro",
      "chars_per_month": 2000000,
      "price_usd": 14.99,
      "price_stars": 750,
      "price_usd_yearly": 107.99,
      "price_stars_yearly": 5400,
      "max_auto_chats": 20,
      "features": ["basic_translate", "inline_mode", "auto_translate", "stats", "priority_support", "gpt_engine"]
    }
  ]
}
```

### POST /billing/checkout
**Request:**
```json
{
  "plan_id": "starter",
  "payment_method": "telegram_stars"
}
```

**Response 200:**
```json
{
  "invoice_url": "https://t.me/$invoice_link",
  "expires_at": "2025-08-20T11:00:00Z"
}
```

---

## 7. Webhook (для Telegram Bot API)

### POST /webhook/telegram
Принимает апдейты от Telegram. Секрет в заголовке `X-Telegram-Bot-Api-Secret-Token`.

---

## 8. Схемы взаимодействия по сценариям

### Сценарий 1: /tr (reply-перевод)

```
User                  Telegram           Bot Service        Backend API        Redis        DeepL
 │                       │                    │                   │               │             │
 │──reply /tr ──────────►│                    │                   │               │             │
 │                       │──webhook ─────────►│                   │               │             │
 │                       │                    │──auth check ─────►│               │             │
 │                       │                    │◄─ user + quota ───│               │             │
 │                       │                    │                   │               │             │
 │                       │                    │──POST /translate ►│               │             │
 │                       │                    │                   │──GET cache ──►│             │
 │                       │                    │                   │◄─ miss ───────│             │
 │                       │                    │                   │──translate ───────────────►│
 │                       │                    │                   │◄─ result ──────────────────│
 │                       │                    │                   │──SET cache ──►│             │
 │                       │                    │                   │──deduct quota │             │
 │                       │                    │◄─ translated ─────│               │             │
 │                       │◄─ sendMessage ─────│                   │               │             │
 │◄─ personal message ───│                    │                   │               │             │
```

### Сценарий 2: Inline query

```
User                  Telegram           Bot Service        Backend API
 │                       │                    │                   │
 │──@bot text ──────────►│                    │                   │
 │                       │──inline_query ────►│                   │
 │                       │                    │──POST /translate  │
 │                       │                    │   (x3 top langs)  │
 │                       │                    │◄─ 3 results ──────│
 │                       │◄─ answerInlineQuery│                   │
 │◄─ dropdown results ───│                    │                   │
 │──выбирает вариант ────►│                    │                   │
 │◄─ msg в чат ──────────│                    │                   │
```

### Сценарий 3: Mini App открывается

```
User             Mini App (React)        Backend API
 │                    │                      │
 │──открыть Mini App ►│                      │
 │                    │──POST /auth/telegram  │
 │                    │   (initData) ────────►│
 │                    │◄─ JWT token ──────────│
 │                    │──GET /users/me ───────►│
 │                    │──GET /stats/me ───────►│
 │                    │──GET /chats ──────────►│
 │                    │◄─ все данные ──────────│
 │◄─ дашборд рендер ──│                       │
```
