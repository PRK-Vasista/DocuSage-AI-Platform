# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
DocuSage AI Service entry point.

This container is a separate AI unit. The main backend never talks to Ollama
directly — it only calls this service over the Docker network.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .core.config import ai_settings
from .core.exceptions import AIServiceError
from .routers import ai as ai_router
from .services.ollama_client import ensure_model_available

_log_level = getattr(logging, str(ai_settings.LOG_LEVEL).upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("ai_service.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown lifecycle for the AI service.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control while the service is running.
    """
    logger.info("AI service starting. Attempting to ensure Ollama model availability.")
    try:
        await ensure_model_available()
    except AIServiceError as exc:
        # Do not crash the container if Ollama is still pulling/warming up.
        logger.warning(
            "Ollama model not ready at startup (%s). "
            "Summarize/chat will retry when requests arrive.",
            exc.message,
        )

    yield
    logger.info("AI service shutting down.")


app = FastAPI(
    title="DocuSage AI Service",
    description=(
        "Isolated AI unit for DocuSage. Provides summarization and "
        "document-grounded chat via a local Ollama runtime."
    ),
    version="0.7.0",
    lifespan=lifespan,
)


@app.exception_handler(AIServiceError)
async def ai_service_exception_handler(request: Request, exc: AIServiceError):
    """
    Translate AI domain errors into HTTP responses.

    Args:
        request: Incoming FastAPI request.
        exc: Raised AI service domain exception.

    Returns:
        JSONResponse: Structured error payload.
    """
    logger.error(
        "AI service error on %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


app.include_router(ai_router.router, prefix="/api/v1/ai")
logger.info("AI service router mounted at /api/v1/ai")


@app.get("/")
def root():
    """
    Simple root health-style endpoint.

    Returns:
        dict: Basic service identity payload.
    """
    return {
        "service": "docu-sage-ai",
        "message": "DocuSage AI Service is running.",
        "model": ai_settings.OLLAMA_MODEL,
        "docs": "/docs",
    }
