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
├── infra/                  ← Docker, docker-compose, nginx конфиги
└── .env.example
```

## Быстрый старт

Документацию смотри в папке `docs/` — начни с `PRD.md`.
