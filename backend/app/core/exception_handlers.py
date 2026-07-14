# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Global exception handlers for DocuSage domain errors.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import DocuSageError

logger = logging.getLogger("core.exception_handlers")


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register application-wide exception handlers on the FastAPI instance.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(DocuSageError)
    async def handle_docusage_error(request: Request, exc: DocuSageError) -> JSONResponse:
        """
        Convert DocuSage domain exceptions into structured JSON HTTP responses.

        Args:
            request: Incoming HTTP request that triggered the exception.
            exc: Raised DocuSage domain exception.

        Returns:
            JSONResponse: Standardized error payload for the client.
        """
        logger.warning(
            "DocuSageError handled: type=%s, status=%s, path=%s, message=%s",
            exc.__class__.__name__,
            exc.status_code,
            request.url.path,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    logger.info("DocuSage domain exception handlers registered.")
