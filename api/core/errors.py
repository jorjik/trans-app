"""Кастомные HTTP-ошибки и обработчики."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """Базовая ошибка приложения с machine-readable кодом."""

    def __init__(self, status_code: int, error: str, message: str, **extra):
        super().__init__(status_code=status_code, detail=message)
        self.error = error
        self.message = message
        self.extra = extra


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "unauthorized", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, "forbidden", message)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, "not_found", f"{resource} not found")


class QuotaExceededError(AppError):
    def __init__(self, chars_used: int, chars_limit: int, reset_at=None):
        super().__init__(
            status.HTTP_402_PAYMENT_REQUIRED,
            "quota_exceeded",
            "Monthly character limit reached",
            chars_used=chars_used,
            chars_limit=chars_limit,
            reset_at=reset_at.isoformat() if reset_at else None,
        )


class RateLimitError(AppError):
    def __init__(self, retry_after: int = 1):
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limit",
            "Too many requests",
            retry_after=retry_after,
        )


class TranslationError(AppError):
    def __init__(self, message: str = "Translation failed"):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, "translation_error", message)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "validation_error", message)


# ── Exception handlers ─────────────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = {"error": exc.error, "message": exc.message}
    body.update(exc.extra)
    return JSONResponse(status_code=exc.status_code, content=body)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import structlog
    log = structlog.get_logger()
    log.error("Unhandled error", path=str(request.url), error=str(exc), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal server error"},
    )
