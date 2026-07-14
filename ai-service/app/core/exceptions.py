# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Domain exceptions for the DocuSage AI service.
"""

import logging

logger = logging.getLogger("ai_service.exceptions")


class AIServiceError(Exception):
    """
    Base exception for AI service failures.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code.
    """

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize an AI service error.

        Args:
            message: Human-readable explanation.
            status_code: HTTP status code for API responses.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        logger.debug(
            "AIServiceError created: type=%s status=%s message=%s",
            self.__class__.__name__,
            status_code,
            message,
        )


class OllamaUnavailableError(AIServiceError):
    """Raised when the Ollama runtime cannot be reached."""

    def __init__(self, message: str = "Ollama service is unavailable."):
        super().__init__(message, status_code=503)
        logger.error("Ollama unavailable: %s", message)


class OllamaInferenceError(AIServiceError):
    """Raised when Ollama inference fails."""

    def __init__(self, message: str = "Ollama inference failed."):
        super().__init__(message, status_code=502)
        logger.error("Ollama inference error: %s", message)


class InvalidAIRequestError(AIServiceError):
    """Raised when summarize/chat input fails validation."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)
        logger.warning("Invalid AI request: %s", message)
