"""
Authentication dependencies for protected API routes.
"""

import logging
from typing import TypedDict

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import auth_utils, models
from ..core.exceptions import DatabaseOperationError
from ..database import get_db

logger = logging.getLogger("dependencies.auth")
logger.setLevel(logging.DEBUG)


class AuthenticatedUser(TypedDict):
    """Typed dictionary returned by the current-user dependency."""

    id: int
    email: str


async def get_current_user(
    token: str = Depends(auth_utils.oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """
    Validate the JWT and load the corresponding user from the database.

    Args:
        token: Bearer token extracted from the Authorization header.
        db: Async SQLAlchemy session.

    Returns:
        AuthenticatedUser: Dictionary containing `id` and `email`.

    Raises:
        HTTPException: 401 if token is invalid or user no longer exists.
        HTTPException: 500 if the database lookup fails unexpectedly.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = await auth_utils.validate_token(token)
        validated_email = token_data.get("email")
        if validated_email is None:
            logger.warning("Token valid but 'sub' (email) claim missing.")
            raise credentials_exception
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error during token processing: %s", exc)
        raise credentials_exception from exc

    try:
        stmt = select(models.User).where(models.User.email == validated_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.error(
            "Database query failed during authenticated user lookup: %s",
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user lookup for authenticated request.",
        ) from exc

    if user is None:
        logger.warning("Authenticated user not found in DB: %s", validated_email)
        raise credentials_exception

    logger.info("Authenticated request resolved for user_id=%s", user.id)
    return {"id": user.id, "email": user.email}
