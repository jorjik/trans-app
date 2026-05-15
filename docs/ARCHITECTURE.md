# ARCHITECTURE — Архитектура TransApp

---

## 1. Обзор системы

```
┌─────────────────────────────────────────────────────────────────┐
│                          TELEGRAM                                │
│  User ──► Bot API ──► Webhook ──► [Bot Service]                 │
│  User ──► Mini App ──────────────► [Backend API]                │
│  User ──► Inline Query ──────────► [Bot Service]                │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       [Bot Service]                  [Backend API]
       Python/aiogram                FastAPI / Python
              │                               │
              └───────────┬───────────────────┘
                          ▼
                   [Translation Service]
                   (внутренний модуль)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         [Google]      [DeepL]     [OpenAI]
         Translate      API         GPT-4o
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
           [Redis]              [PostgreSQL]
           кэш + RL              основная БД
```

---

## 2. Модули и их ответственность

### 2.1 Bot Service (`/bot`)

```
bot/
├── handlers/
│   ├── start.py          # /start, регистрация, приветствие
│   ├── translate.py      # /tr, /to — команды перевода
│   ├── settings.py       # /lang, /quota
│   ├── group.py          # /group_translate
│   └── inline.py         # inline query handler
├── middlewares/
│   ├── auth.py           # проверка регистрации пользователя
│   ├── rate_limit.py     # Redis-based rate limiting
│   └── quota_check.py    # проверка баланса перед переводом
├── keyboards/
│   ├── inline_kb.py      # inline-кнопки
│   └── reply_kb.py       # reply-кнопки (если нужны)
├── services/
│   └── api_client.py     # HTTP-клиент к Backend API
└── main.py               # запуск бота, регистрация роутеров
```

**Ответственность Bot Service:**
- Получение апдейтов от Telegram (webhook / polling)
- Парсинг команд и inline-запросов
- Проверка квоты ПЕРЕД отправкой в API (через middleware)
- Форматирование ответов пользователю
- НЕ работает с БД напрямую — только через Backend API

---

### 2.2 Backend API (`/api`)

```
api/
├── routers/
│   ├── auth.py           # POST /auth/telegram — валидация initData
│   ├── translate.py      # POST /translate
│   ├── users.py          # GET/PATCH /users/me — настройки
│   ├── chats.py          # CRUD /chats — авто-переводы
│   ├── stats.py          # GET /stats/me — статистика
│   ├── billing.py        # GET /plans, POST /billing/checkout
│   └── webhook.py        # POST /webhook/telegram — входящие от TG
├── services/
│   ├── translation/
│   │   ├── base.py       # абстрактный TranslationProvider
│   │   ├── google.py     # Google Translate Cloud API
│   │   ├── deepl.py      # DeepL API
│   │   ├── openai.py     # OpenAI / GPT-4o mini
│   │   └── router.py     # выбор провайдера + fallback
│   ├── cache.py          # Redis: кэш переводов, rate limiting
│   ├── quota.py          # подсчёт символов, списание, пополнение
│   ├── billing.py        # интеграция платёжных провайдеров
│   └── language_detect.py # определение языка источника
├── models/               # SQLAlchemy ORM модели
│   ├── user.py
│   ├── translation_log.py
│   ├── chat_config.py
│   └── billing.py
├── db/
│   ├── session.py        # async engine + sessionmaker
│   └── migrations/       # Alembic миграции
├── core/
│   ├── config.py         # Pydantic Settings (env vars)
│   ├── security.py       # HMAC валидация, шифрование
│   └── errors.py         # кастомные HTTP-ошибки
└── main.py               # FastAPI app, lifespan, CORS
```

---

### 2.3 Translation Service (внутренний модуль API)

```
Логика выбора провайдера:

1. Проверить кэш Redis (ключ: sha256(text + src + tgt))
   → Если есть: вернуть из кэша, НЕ списывать символы

2. Определить язык источника (если auto-detect):
   → fasttext/langdetect локально (быстро, бесплатно)
   → fallback: Google Language Detection API

3. Выбрать провайдера:
   User.preferred_engine → если не задан:
   - текст < 5000 символов → DeepL (качество)
   - текст > 5000 символов → Google Translate (дешевле)
   - специальные языки (нет в DeepL) → Google
   - "premium перевод" (контекстный) → GPT-4o mini

4. Отправить запрос с retry (3 попытки, backoff 1s/2s/4s)
   → Если провайдер недоступен: fallback на следующий в списке

5. Записать в кэш (TTL: 24 часа для коротких, 7 дней для длинных)

6. Списать символы с баланса пользователя

7. Записать в translation_log (без текста, только метаданные)
```

---

## 3. Схема базы данных

### users
```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    telegram_id     BIGINT UNIQUE NOT NULL,  -- зашифрован AES в коде
    telegram_id_hash VARCHAR(64) UNIQUE NOT NULL,  -- sha256 для lookup
    username        VARCHAR(64),             -- опционально
    language_code   VARCHAR(10) DEFAULT 'en',-- язык TG клиента
    target_language VARCHAR(10) DEFAULT 'en',-- куда переводить по умолчанию
    preferred_engine VARCHAR(20) DEFAULT 'auto',
    favorite_langs  JSONB DEFAULT '[]',      -- ["en","de","fr"]
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### quotas
```sql
CREATE TABLE quotas (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    plan            VARCHAR(20) DEFAULT 'free',  -- free|starter|pro|business
    chars_limit     INTEGER DEFAULT 50000,       -- символов в месяц
    chars_used      INTEGER DEFAULT 0,
    reset_at        TIMESTAMPTZ,                 -- дата сброса
    group_id        BIGINT,                      -- для group-тарифа
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);
```

### chat_configs (авто-переводы)
```sql
CREATE TABLE chat_configs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
    chat_id         BIGINT NOT NULL,
    chat_username   VARCHAR(128),
    chat_title      VARCHAR(256),
    source_lang     VARCHAR(10) DEFAULT 'auto',
    target_lang     VARCHAR(10) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_synced_at  TIMESTAMPTZ,
    last_message_id BIGINT,                      -- для пагинации
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_configs_user_id ON chat_configs(user_id);
CREATE INDEX idx_chat_configs_active ON chat_configs(user_id) WHERE is_active = TRUE;
```

### translation_logs
```sql
CREATE TABLE translation_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id),
    source_lang     VARCHAR(10),
    target_lang     VARCHAR(10),
    char_count      INTEGER NOT NULL,
    provider        VARCHAR(20),             -- google|deepl|openai
    latency_ms      INTEGER,
    cached          BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20),             -- success|error|limit_exceeded
    error_code      VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Партиционирование по месяцам (когда данных много)
CREATE INDEX idx_tlog_user_date ON translation_logs(user_id, created_at);
```

### plans
```sql
CREATE TABLE plans (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(20) UNIQUE NOT NULL,  -- free|starter|pro|business
    chars_per_month INTEGER NOT NULL,
    price_usd       DECIMAL(8,2),
    price_stars     INTEGER,                      -- Telegram Stars
    max_auto_chats  INTEGER DEFAULT 5,
    features        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE
);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id),
    plan_id         INTEGER REFERENCES plans(id),
    status          VARCHAR(20),             -- active|cancelled|expired
    started_at      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    payment_provider VARCHAR(20),            -- telegram_stars|stripe|yookassa
    external_id     VARCHAR(128),            -- ID в платёжной системе
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Кэширование (Redis)

```
Структура ключей:

# Кэш перевода (главная экономия)
translate:cache:{sha256(text+src_lang+tgt_lang+engine)}
TTL: 86400 (24ч) для коротких текстов
TTL: 604800 (7 дней) для длинных (>500 символов)
Значение: JSON {translated_text, provider, created_at}

# Rate limiting (per user)
ratelimit:user:{user_id}:translate
TTL: 1 сек (sliding window)
Значение: счётчик (INCR + EXPIRE)

# Rate limiting (global, anti-abuse)
ratelimit:global:translate
TTL: 1 сек

# Сессии Mini App (временный токен после валидации initData)
session:miniapp:{token}
TTL: 3600 (1 час)
Значение: JSON {user_id, telegram_id}

# Очередь авто-переводов (опционально, для Celery/RQ)
queue:auto_translate
Значение: list of {user_id, chat_id, message_ids[]}
```

---

## 5. Стек технологий

### Backend (Bot + API)
```
Язык:        Python 3.12
Bot:         aiogram 3.x (async, webhook-ready)
API:         FastAPI + Uvicorn (ASGI)
ORM:         SQLAlchemy 2.0 (async) + Alembic
DB:          PostgreSQL 16
Cache:       Redis 7
Task queue:  Celery + Redis (для авто-переводов, не нужен в v1)
HTTP client: httpx (async)
Валидация:   Pydantic v2
Логи:        structlog → JSON
```

### Mini App
```
Framework:   React 18 + TypeScript
Build:       Vite
UI:          Mantine UI (готовые компоненты, TG-тема)
State:       Zustand (лёгкий)
API client:  TanStack Query (кэш + retry)
TG SDK:      @twa-dev/sdk
Деплой:      Nginx static / Cloudflare Pages
```

### Инфра
```
Контейнеры:  Docker + Docker Compose
Reverse proxy: Nginx (SSL termination)
SSL:         Certbot / Let's Encrypt
Хостинг MVP: VPS 2 CPU / 4GB RAM (DigitalOcean / Hetzner)
CI/CD:       GitHub Actions → SSH deploy
Мониторинг:  Grafana + Prometheus (или Betterstack для MVP)
```

### MT-провайдеры (в порядке приоритета)
```
1. DeepL API Free  → до 500k символов/мес бесплатно
2. Google Cloud Translation API → pay-as-you-go ($20/1M символов)
3. OpenAI GPT-4o mini → для контекстного перевода ($0.15/1M input tokens)
```
