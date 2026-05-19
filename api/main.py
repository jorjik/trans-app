"""
TransApp Backend API — точка входа FastAPI.

Запуск (dev):
    uvicorn main:app --reload --port 8000

Запуск (prod):
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
"""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
)
from db.session import engine, Base
from services.cache import get_redis, close_redis
from routers import auth, translate, users, chats, stats, billing, webhook


# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.dev.ConsoleRenderer()
            if settings.env == "development"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(message)s",
    )


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = structlog.get_logger()
    log.info("Starting TransApp API", env=settings.env)

    # Создаём таблицы если их нет (idempotent — не трогает существующие)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created / verified")

    # Подключаемся к Redis
    await get_redis()

    yield  # ← приложение работает здесь

    # Graceful shutdown
    await close_redis()
    await engine.dispose()
    log.info("TransApp API stopped")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TransApp API",
    description="Personal Telegram Translator — Backend API",
    version="1.0.0",
    docs_url="/docs" if settings.env == "development" else None,
    redoc_url="/redoc" if settings.env == "development" else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# Роутеры
app.include_router(auth.router)
app.include_router(translate.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(stats.router)
app.include_router(billing.router)
app.include_router(webhook.router)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health() -> dict:
    """Проверка работоспособности сервиса."""
    from services.cache import get_redis as _get_redis
    redis_ok = False
    try:
        r = await _get_redis()
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "env": settings.env,
        "redis": "ok" if redis_ok else "unavailable",
    }


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "TransApp API", "version": "1.0.0", "docs": "/docs"}
