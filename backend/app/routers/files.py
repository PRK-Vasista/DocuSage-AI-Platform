"""
Document file management API routes for DocuSage.
"""

import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import DocuSageError
from ..database import get_db
from ..dependencies.auth import AuthenticatedUser, get_current_user
from ..schemas.document_schemas import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
)
from ..services import document_service

router = APIRouter(tags=["Files"])
logger = logging.getLogger("files_router")
logger.setLevel(logging.DEBUG)


@router.post("/upload", response_model=DocumentResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a new document for the authenticated user.

    Args:
        file: Uploaded multipart file.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        DocumentResponse: Metadata for the stored document.
    """
    logger.info(
        "Upload request received from user_id=%s, filename=%s",
        current_user["id"],
        file.filename,
    )
    try:
        return await document_service.upload_document(
            db=db,
            user_id=current_user["id"],
            file=file,
        )
    except DocuSageError:
        raise


@router.get("/", response_model=DocumentListResponse)
async def list_files(
    include_deleted: bool = Query(
        default=False,
        description="When true, include soft-deleted documents (trash).",
    ),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    List documents owned by the authenticated user.

    Args:
        include_deleted: Whether to include soft-deleted documents.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        DocumentListResponse: Document list and storage quota summary.
    """
    logger.info(
        "List request from user_id=%s, include_deleted=%s",
        current_user["id"],
        include_deleted,
    )
    try:
        return await document_service.list_user_documents(
            db=db,
            user_id=current_user["id"],
            include_deleted=include_deleted,
        )
    except DocuSageError:
        raise


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_file_metadata(
    document_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Retrieve metadata for a single user-owned document.

    Args:
        document_id: Document identifier.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        DocumentResponse: Document metadata.
    """
    logger.info(
        "Metadata request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        return await document_service.get_document_metadata(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
        )
    except DocuSageError:
        raise


@router.get("/{document_id}/download")
async def download_file(
    document_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Download the binary content of a user-owned document.

    Args:
        document_id: Document identifier.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        Response: Raw file bytes with appropriate content headers.
    """
    logger.info(
        "Download request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        content, metadata = await document_service.get_document_download(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
        )
    except DocuSageError:
        raise

    return Response(
        content=content,
        media_type=metadata.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{metadata.filename}"'
        },
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def soft_delete_file(
    document_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDeleteResponse:
    """
    Soft-delete a document by moving it to the user's trash.

    Args:
        document_id: Document identifier.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        DocumentDeleteResponse: Deletion confirmation payload.
    """
    logger.info(
        "Soft delete request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        await document_service.soft_delete_document(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
        )
    except DocuSageError:
        raise

    return DocumentDeleteResponse(
        message="Document moved to trash.",
        document_id=document_id,
        deletion_type="soft",
    )


@router.delete("/{document_id}/permanent", response_model=DocumentDeleteResponse)
async def permanently_delete_file(
    document_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDeleteResponse:
    """
    Permanently delete a document that has already been soft-deleted.

    Args:
        document_id: Document identifier.
        current_user: Authenticated user dependency.
        db: Async SQLAlchemy session.

    Returns:
        DocumentDeleteResponse: Permanent deletion confirmation payload.
    """
    logger.info(
        "Permanent delete request for document_id=%s by user_id=%s",
        document_id,
        current_user["id"],
    )
    try:
        await document_service.permanently_delete_document(
            db=db,
            user_id=current_user["id"],
            document_id=document_id,
        )
    except DocuSageError:
        raise

    return DocumentDeleteResponse(
        message="Document permanently deleted.",
        document_id=document_id,
        deletion_type="permanent",
    )
