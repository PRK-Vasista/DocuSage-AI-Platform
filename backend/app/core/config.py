"""
Centralized application configuration for DocuSage.

All environment-driven settings and business-rule constants (upload limits,
allowed file types, storage paths) are defined here so that routers and
services remain decoupled from hard-coded values.
"""

import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger("core.config")
logger.setLevel(logging.DEBUG)


class AppSettings(BaseSettings):
    """
    Loads runtime configuration from environment variables with safe defaults
    suitable for local Docker development.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/docu_sage_db"

    # --- Security / Auth ---
    SECRET_KEY: str = "please-change-this-to-a-long-random-string-in-next-sprint"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # --- File Storage ---
    UPLOAD_DIR: str = "user_uploads"
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024              # 10 MB per upload
    MAX_USER_STORAGE_BYTES: int = 1024 * 1024 * 1024        # 1 GB total per user
    MAX_EXTRACTED_TEXT_BYTES: int = 5 * 1024 * 1024         # 5 MB raw text during extraction
    MAX_STORED_SUMMARY_BYTES: int = 1 * 1024 * 1024          # 1 MB summarized text stored in DB
    SUMMARY_TARGET_CHAR_COUNT: int = 4000                   # Target / fallback extractive length

    # --- Isolated AI unit (ai-service container) ---
    AI_SERVICE_URL: str = "http://ai-service:8100"
    AI_SERVICE_TIMEOUT_SECONDS: float = 180.0
    AI_SERVICE_ENABLED: bool = True
    AI_FALLBACK_TO_EXTRACTIVE: bool = True  # Use local extractive summary if AI unit is down
    CHAT_HISTORY_LIMIT: int = 20

    # --- Database Migrations (Alembic) ---
    ENABLE_ALEMBIC_MIGRATIONS: bool = True
    ENABLE_CREATE_ALL_FALLBACK: bool = True
    DB_MIGRATION_MAX_RETRIES: int = 5
    DB_MIGRATION_RETRY_SECONDS: int = 2

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        case_sensitive = True


# Singleton settings instance consumed by services and dependencies.
app_settings = AppSettings()
logger.info(
    "Application settings loaded. Upload limit=%s bytes, user quota=%s bytes.",
    app_settings.MAX_FILE_SIZE_BYTES,
    app_settings.MAX_USER_STORAGE_BYTES,
)


# --- Allowed MIME types for text-based document uploads ---
ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
})

# Any MIME type beginning with "text/" is treated as a text-based file.
TEXT_MIME_PREFIX: str = "text/"

# --- Allowed file extensions (secondary validation layer) ---
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
    ".docx",
    ".csv",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".rtf",
    ".log",
})

logger.debug("Allowed MIME types: %s", sorted(ALLOWED_MIME_TYPES))
logger.debug("Allowed extensions: %s", sorted(ALLOWED_EXTENSIONS))


# --- Document processing status values ---
PROCESSING_STATUS_UPLOADED: str = "uploaded"
PROCESSING_STATUS_PROCESSING: str = "processing"
PROCESSING_STATUS_READY: str = "ready"
PROCESSING_STATUS_FAILED: str = "failed"
