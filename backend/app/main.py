# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
DocuSage FastAPI application entry point.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.config import app_settings
from .core.exception_handlers import register_exception_handlers
from .database import AsyncSessionLocal, init_db
from .middleware.rate_limit import RateLimitMiddleware
from .routers import auth, chat, files
from .services import ai_client_service

_log_level = getattr(logging, str(app_settings.LOG_LEVEL).upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown lifecycle events.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control returns to FastAPI while the app is running.
    """
    logger.info("Application lifespan start: initializing services.")
    db_ready = await init_db()
    if db_ready:
        logger.info("Database initialization complete.")
    else:
        logger.critical(
            "Database initialization failed during startup. "
            "The API may reject database-dependent requests until resolved."
        )

    yield

    logger.info("Application lifespan end: shutting down.")


app = FastAPI(
    title="DocuSage AI Platform",
    description=(
        "Backend service with authentication, document upload, storage quota "
        "enforcement, soft/permanent deletion, background processing, and "
        "proxied AI summarization/chat via an isolated AI service unit."
    ),
    version="0.9.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

register_exception_handlers(app)

logger.info("Including authentication, files, and chat routers...")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(files.router, prefix="/api/v1/files")
app.include_router(chat.router, prefix="/api/v1/chat")
logger.info("Routers successfully included.")


@app.get("/")
def read_root():
    """
    Simple identity endpoint.

    Returns:
        dict: Basic service status message.
    """
    logger.debug("Root endpoint accessed successfully.")
    return {
        "message": "DocuSage Backend is Running! Check /docs for API details."
    }


@app.get("/health")
async def health():
    """
    Liveness/readiness-style health check for Compose and operators.

    Returns:
        dict: Database and AI unit reachability summary.
    """
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:  # noqa: BLE001 — health must not raise
        logger.warning("Health DB check failed: %s", exc)

    ai_status = "disabled"
    if app_settings.AI_SERVICE_ENABLED:
        try:
            ai_payload = await ai_client_service.check_ai_health()
            ai_status = ai_payload.get("status", "unknown")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Health AI check failed: %s", exc)
            ai_status = "unreachable"

    overall = "ok" if db_ok and ai_status in {"ok", "disabled", "degraded"} else "degraded"
    if not db_ok:
        overall = "unhealthy"

    return {
        "status": overall,
        "database": "ok" if db_ok else "unavailable",
        "ai_service": ai_status,
        "env": app_settings.APP_ENV,
    }
