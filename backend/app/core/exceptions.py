"""
Custom domain exceptions for DocuSage.

These exceptions represent predictable business-rule failures. Routers and
exception handlers translate them into appropriate HTTP responses.
"""

import logging

logger = logging.getLogger("core.exceptions")
logger.setLevel(logging.DEBUG)


class DocuSageError(Exception):
    """
    Base exception for all DocuSage domain errors.

    Attributes:
        message: Human-readable explanation of the failure.
        status_code: Suggested HTTP status code for API responses.
    """

    def __init__(self, message: str, status_code: int = 400):
        """
        Initialize a DocuSage domain exception.

        Args:
            message: Human-readable error description.
            status_code: HTTP status code that maps to this error.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        logger.debug(
            "DocuSageError created: type=%s, status=%s, message=%s",
            self.__class__.__name__,
            status_code,
            message,
        )


class FileValidationError(DocuSageError):
    """Raised when an uploaded file fails generic validation checks."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class UnsupportedFileTypeError(FileValidationError):
    """Raised when the uploaded file MIME type or extension is not allowed."""

    def __init__(self, message: str):
        super().__init__(message)
        logger.warning("Unsupported file type rejected: %s", message)


class FileSizeExceededError(FileValidationError):
    """Raised when a single upload exceeds the per-file size limit."""

    def __init__(self, message: str):
        super().__init__(message)
        logger.warning("File size limit exceeded: %s", message)


class StorageQuotaExceededError(DocuSageError):
    """Raised when a user exceeds their total storage quota."""

    def __init__(self, message: str):
        super().__init__(message, status_code=413)
        logger.warning("User storage quota exceeded: %s", message)


class DocumentNotFoundError(DocuSageError):
    """Raised when a requested document does not exist or is inaccessible."""

    def __init__(self, message: str = "Document not found."):
        super().__init__(message, status_code=404)
        logger.warning("Document not found: %s", message)


class DocumentAlreadyDeletedError(DocuSageError):
    """Raised when an operation targets a document that is already soft-deleted."""

    def __init__(self, message: str = "Document is already in the trash."):
        super().__init__(message, status_code=409)
        logger.warning("Document already soft-deleted: %s", message)


class DocumentNotSoftDeletedError(DocuSageError):
    """Raised when permanent deletion is attempted before soft deletion."""

    def __init__(
        self,
        message: str = "Document must be soft-deleted before permanent deletion.",
    ):
        super().__init__(message, status_code=409)
        logger.warning("Permanent delete blocked: %s", message)


class FileStorageError(DocuSageError):
    """Raised when reading from or writing to the filesystem fails."""

    def __init__(self, message: str = "File storage operation failed."):
        super().__init__(message, status_code=500)
        logger.error("File storage error: %s", message)


class DatabaseOperationError(DocuSageError):
    """Raised when a database query or transaction fails unexpectedly."""

    def __init__(self, message: str = "A database operation failed."):
        super().__init__(message, status_code=500)
        logger.error("Database operation error: %s", message)


class TextExtractionError(DocuSageError):
    """Raised when text cannot be extracted from an uploaded document."""

    def __init__(self, message: str = "Failed to extract text from the document."):
        super().__init__(message, status_code=422)
        logger.error("Text extraction error: %s", message)


class SummarizationError(DocuSageError):
    """Raised when document summarization fails."""

    def __init__(self, message: str = "Failed to summarize document content."):
        super().__init__(message, status_code=422)
        logger.error("Summarization error: %s", message)


class DocumentProcessingError(DocuSageError):
    """Raised when the end-to-end document processing pipeline fails."""

    def __init__(self, message: str = "Document processing failed."):
        super().__init__(message, status_code=500)
        logger.error("Document processing error: %s", message)


class AlembicRevisionIdError(DocuSageError):
    """Raised when an Alembic revision ID exceeds the database column limit."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)
        logger.critical("Alembic revision ID validation failed: %s", message)


class AIServiceClientError(DocuSageError):
    """Raised when the isolated AI service unit cannot fulfill a request."""

    def __init__(self, message: str = "AI service request failed."):
        super().__init__(message, status_code=503)
        logger.error("AI service client error: %s", message)


class DocumentNotReadyError(DocuSageError):
    """Raised when chat is attempted before processing completes."""

    def __init__(self, message: str = "Document is not ready for chat yet."):
        super().__init__(message, status_code=409)
        logger.warning("Document not ready for chat: %s", message)


class ChatError(DocuSageError):
    """Raised when document chat persistence or orchestration fails."""

    def __init__(self, message: str = "Document chat request failed."):
        super().__init__(message, status_code=500)
        logger.error("Chat error: %s", message)
