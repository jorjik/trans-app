# TransApp — Глобальный переводчик поверх Telegram

> Личный переводчик прямо в Telegram: переводи входящие/исходящие, не засоряя общий чат.

## Структура репозитория

```
trans-app/
├── docs/
│   ├── PRD.md              ← Продуктовые требования (пользовательские сценарии)
│   ├── TZ.md               ← Техническое задание v1
│   ├── ARCHITECTURE.md     ← Архитектура, модули, БД
│   ├── API.md              ← Схема API и взаимодействие компонентов
│   └── MONETIZATION.md     ← Монетизация, тарифы, анти-абуз
├── bot/                    ← Telegram Bot (Python / Node.js)
├── api/                    ← Backend API (FastAPI / Express)
├── miniapp/                ← Telegram Mini App (React/Vite)
├── infra/                  ← dev docker-compose
├── docker-compose.coolify.yml  ← прод-стек для Coolify
└── .env.example
```

## Быстрый старт

Документацию смотри в папке `docs/` — начни с `PRD.md`.

## Деплой (Coolify)

Прод разворачивается одним Docker Compose стеком на Coolify:
`docker-compose.coolify.yml`. Полная инструкция — `docs/DEPLOY-COOLIFY.md`.

Локальная разработка — `infra/docker-compose.yml`.
