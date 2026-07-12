"""
DocuSage FastAPI application entry point.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.exception_handlers import register_exception_handlers
from .database import init_db
from .routers import auth, chat, files

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
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
    title="DocuSage AI Platform (v0.5 - AI Summarization & Chat)",
    description=(
        "Backend service with authentication, document upload, storage quota "
        "enforcement, soft/permanent deletion, background processing, and "
        "proxied AI summarization/chat via an isolated AI service unit."
    ),
    version="0.5.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

logger.info("Including authentication, files, and chat routers...")
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(files.router, prefix="/api/v1/files")
app.include_router(chat.router, prefix="/api/v1/chat")
logger.info("Routers successfully included.")


@app.get("/")
def read_root():
    """
    Simple health-style root endpoint.

    Returns:
        dict: Basic service status message.
    """
    logger.debug("Root endpoint accessed successfully.")
    return {
        "message": "DocuSage Backend is Running! Check /docs for API details."
    }
