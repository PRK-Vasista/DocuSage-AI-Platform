# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Configuration for the DocuSage AI service unit.

This service is intentionally isolated from the main backend. It only talks to
Ollama and exposes summarize/chat HTTP APIs for the backend to call.
"""

import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger("ai_service.config")


class AIServiceSettings(BaseSettings):
    """
    Runtime settings for the AI service and its Ollama dependency.

    Attributes:
        APP_ENV: Runtime environment label.
        LOG_LEVEL: Root logging level name.
        OLLAMA_BASE_URL: Base URL of the Ollama container.
        OLLAMA_MODEL: Local model name to use for inference.
        OLLAMA_TIMEOUT_SECONDS: HTTP timeout for Ollama calls.
        MAX_CONTEXT_CHARS: Max characters of document context sent to the model.
        MAX_SUMMARY_CHARS: Target maximum length for generated summaries.
        OLLAMA_PULL_ON_STARTUP: Whether to request a model pull on startup.
    """

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0
    MAX_CONTEXT_CHARS: int = 12000
    MAX_SUMMARY_CHARS: int = 4000
    OLLAMA_PULL_ON_STARTUP: bool = True

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        case_sensitive = True


ai_settings = AIServiceSettings()
logger.info(
    "AI service settings loaded. env=%s ollama=%s model=%s",
    ai_settings.APP_ENV,
    ai_settings.OLLAMA_BASE_URL,
    ai_settings.OLLAMA_MODEL,
)
