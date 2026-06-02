"""
JWT and password utility functions for DocuSage authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .core.config import app_settings

logger = logging.getLogger("auth_utils")
logger.setLevel(logging.DEBUG)

# Argon2 is the recommended modern password hashing scheme.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
logger.debug("Password CryptContext initialized with Argon2.")

# OAuth2 bearer token extractor used by protected routes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
logger.info("Auth utilities loaded successfully.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its stored Argon2 hash.

    Args:
        plain_password: Password supplied by the user.
        hashed_password: Stored password hash.

    Returns:
        bool: True if the password matches the hash.
    """
    logger.debug("Attempting password verification.")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain-text password to hash.

    Returns:
        str: Generated password hash.
    """
    logger.debug("Hashing password with Argon2.")
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Claims to encode into the token payload.
        expires_delta: Optional custom expiration interval.

    Returns:
        str: Encoded JWT string.

    Raises:
        HTTPException: If token encoding fails due to configuration issues.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            app_settings.SECRET_KEY,
            algorithm=app_settings.ALGORITHM,
        )
        logger.debug("JWT token successfully created. Expires: %s", expire)
        return encoded_jwt
    except Exception as exc:
        logger.critical(
            "Fatal error creating JWT token. Check SECRET_KEY or ALGORITHM settings: %s",
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security mechanism failed. Cannot issue token.",
        ) from exc


async def validate_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Decode and validate a JWT bearer token.

    Args:
        token: Bearer token extracted from the Authorization header.

    Returns:
        dict: Decoded token payload subset containing the user's email.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Token is invalid or expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            app_settings.SECRET_KEY,
            algorithms=[app_settings.ALGORITHM],
        )
        email: str = payload.get("sub")

        if email is None:
            logger.warning("Token decoded successfully, but 'sub' claim was missing.")
            raise credentials_exception

    except JWTError as exc:
        logger.warning(
            "JWT validation failed. Type: %s, Detail: %s",
            exc.__class__.__name__,
            exc,
        )
        raise credentials_exception from exc
    except Exception as exc:
        logger.error("Unexpected error during token processing: %s", exc)
        raise credentials_exception from exc

    logger.info("Token successfully validated for user: %s", email)
    return {"email": email}
