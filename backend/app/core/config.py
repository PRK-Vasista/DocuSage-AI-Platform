# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Centralized application configuration for DocuSage.

All environment-driven settings and business-rule constants (upload limits,
allowed file types, storage paths) are defined here so that routers and
services remain decoupled from hard-coded values.
"""

import logging
import sys
from urllib.parse import urlparse

from pydantic_settings import BaseSettings

logger = logging.getLogger("core.config")

_WEAK_SECRET_KEY = "please-change-this-to-a-long-random-string-in-next-sprint"
_SAMPLE_DB_PASSWORD = "password"


class AppSettings(BaseSettings):
    """
    Loads runtime configuration from environment variables with safe defaults
    suitable for local Docker development.
    """

    # --- Runtime ---
    APP_ENV: str = "development"  # development | production
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = (
        "http://localhost,http://localhost:3000,http://127.0.0.1:3000"
    )
    PUBLIC_APP_URL: str = "http://localhost:3000"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/docu_sage_db"

    # --- Security / Auth ---
    SECRET_KEY: str = _WEAK_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # --- Optional SMTP (password reset). Empty SMTP_HOST disables mail. ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

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

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def smtp_configured(self) -> bool:
        """Return True when SMTP_HOST is set for outbound mail."""
        return bool(self.SMTP_HOST and self.SMTP_HOST.strip())

    def validate_production_secrets(self) -> None:
        """
        Refuse to run in production with sample/weak secrets.

        Raises:
            SystemExit: When APP_ENV=production and secrets are unsafe.
        """
        if self.APP_ENV.lower() != "production":
            return

        errors: list[str] = []
        if not self.SECRET_KEY or self.SECRET_KEY == _WEAK_SECRET_KEY or len(self.SECRET_KEY) < 32:
            errors.append(
                "SECRET_KEY must be set to a strong random string "
                "(at least 32 characters) when APP_ENV=production."
            )

        parsed = urlparse(self.DATABASE_URL)
        db_password = parsed.password or ""
        if db_password == _SAMPLE_DB_PASSWORD:
            errors.append(
                "DATABASE_URL must not use the sample password "
                f"'{_SAMPLE_DB_PASSWORD}' when APP_ENV=production."
            )

        if errors:
            for message in errors:
                logger.critical(message)
            sys.exit(1)


# Singleton settings instance consumed by services and dependencies.
app_settings = AppSettings()
app_settings.validate_production_secrets()
logger.info(
    "Application settings loaded. env=%s Upload limit=%s bytes, user quota=%s bytes.",
    app_settings.APP_ENV,
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
