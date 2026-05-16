"""TransApp Backend API вЂ” С‚РѕС‡РєР° РІС…РѕРґР°."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.errors import (
    AppError, app_error_handler,
    http_error_handler, unhandled_error_handler,
)
from db.session import engine, Base
from services.cache import get_redis, close_redis
from routers import auth, translate, users, chats, stats, billing, webhook


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer() if settings.env == "development"
            else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log = structlog.get_logger()
    log.info("Starting TransApp API", env=settings.env)

    # РЎРѕР·РґР°С‘Рј С‚Р°Р±Р»РёС†С‹ (РІ production вЂ” С‚РѕР»СЊРєРѕ С‡РµСЂРµР· Alembic!)
    if settings.env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("DB tables ensured (dev mode)")

    # Redis
    redis = await get_redis()
    log.info("Redis", connected=redis is not None)

    yield

    await close_redis()
    await engine.dispose()
    log.info("TransApp API stopped")


app = FastAPI(
    title="TransApp API",
    version="1.0.0",
    description="Personal Telegram translator backend",
    lifespan=lifespan,
    docs_url="/docs" if settings.env == "development" else None,
    redoc_url=None,
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

# Routers
app.include_router(auth.router)
app.include_router(translate.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(stats.router)
app.include_router(billing.router)
app.include_router(webhook.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}