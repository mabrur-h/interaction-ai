from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .logging_config import configure_logging, logger
from .routes import api_router, api_router_v2
from .services import get_important_email_watcher, get_trigger_scheduler


# Register global exception handlers for consistent error responses across the API
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.debug("validation error", extra={"errors": exc.errors(), "path": str(request.url)})
        return JSONResponse(
            {"ok": False, "error": "Invalid request", "detail": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        logger.debug(
            "http error",
            extra={"detail": exc.detail, "status": exc.status_code, "path": str(request.url)},
        )
        detail = exc.detail
        if not isinstance(detail, str):
            detail = json.dumps(detail)
        return JSONResponse({"ok": False, "error": detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"path": str(request.url)})
        return JSONResponse(
            {"ok": False, "error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


configure_logging()
_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup: Initialize background services
    logger.info("Starting OpenPoke server", extra={"version": _settings.app_version})

    scheduler = get_trigger_scheduler()
    await scheduler.start()

    watcher = get_important_email_watcher()
    await watcher.start()

    logger.info("Background services started")

    yield  # Application is running

    # Shutdown: Gracefully stop services
    logger.info("Shutting down OpenPoke server")

    await scheduler.stop()
    await watcher.stop()

    logger.info("Background services stopped")


app = FastAPI(
    title=_settings.app_name,
    version=_settings.app_version,
    docs_url=_settings.resolved_docs_url,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS middleware with production-ready settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_allow_origins,
    allow_credentials=True,  # Required for auth cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Request-ID"],
    max_age=86400,  # Cache preflight for 24 hours
)

register_exception_handlers(app)

# Include both v1 (legacy) and v2 (authenticated) routers
app.include_router(api_router)
app.include_router(api_router_v2)


__all__ = ["app"]
