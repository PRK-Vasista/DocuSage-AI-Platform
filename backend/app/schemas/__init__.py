"""
Pydantic request/response schemas for DocuSage API endpoints.

Schemas are grouped by domain and re-exported from this package to keep router
imports concise and consistent.
"""

from .auth_schemas import Token, TokenData, UserCreate
from .document_schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    StorageQuotaResponse,
)

__all__ = [
    "UserCreate",
    "Token",
    "TokenData",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentDeleteResponse",
    "StorageQuotaResponse",
]
