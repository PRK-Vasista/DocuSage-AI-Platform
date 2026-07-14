# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Authentication API routes for DocuSage.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import auth_utils, models, schemas
from ..core.config import app_settings
from ..database import get_db
from ..dependencies.auth import AuthenticatedUser, get_current_user
from ..services.email_service import EmailDeliveryError, send_email

router = APIRouter(tags=["Auth"])
logger = logging.getLogger("auth_router")

_GENERIC_FORGOT_MESSAGE = (
    "If an account exists for that email and email delivery is configured, "
    "a reset link has been sent."
)
_RESET_TOKEN_TTL = timedelta(hours=1)


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@router.post("/register", response_model=schemas.Token)
async def register_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user, hash their password, and issue a JWT access token.

    Args:
        user_data: Registration payload containing email and password.
        db: Async SQLAlchemy session.

    Returns:
        Token: Newly issued JWT access token.
    """
    logger.info("Registration attempt for email=%s", user_data.email)

    try:
        stmt = select(models.User).where(models.User.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.error(
            "Database error during registration check for %s: %s",
            user_data.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user existence check. See backend logs.",
        ) from exc

    if existing_user:
        logger.warning("Registration failed: email already registered: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = auth_utils.get_password_hash(user_data.password)
    new_user = models.User(email=user_data.email, password_hash=hashed_password)

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(
            "Registration success: user_id=%s, email=%s",
            new_user.id,
            new_user.email,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.critical(
            "Failed to commit new user %s to DB. Rollback initiated: %s",
            user_data.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to a critical database error.",
        ) from exc

    access_token = auth_utils.create_access_token(data={"sub": new_user.email})
    return schemas.Token(access_token=access_token)


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user and issue a JWT access token.

    Args:
        user_data: Login payload containing email and password.
        db: Async SQLAlchemy session.

    Returns:
        Token: JWT access token for the authenticated user.
    """
    logger.info("Login attempt for email=%s", user_data.email)

    try:
        stmt = select(models.User).where(models.User.email == user_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.error("Database error during login for %s: %s", user_data.email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user lookup. See backend logs.",
        ) from exc

    if not user:
        logger.warning("Login failed: user not found for email=%s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth_utils.verify_password(user_data.password, user.password_hash):
        logger.warning("Login failed: password mismatch for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_utils.create_access_token(data={"sub": user.email})
    logger.info("Login success for email=%s", user.email)
    return schemas.Token(access_token=access_token)


@router.get("/me", response_model=schemas.TokenData)
async def read_users_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Return the authenticated user's email to verify JWT validity.

    Args:
        current_user: Authenticated user dependency.

    Returns:
        TokenData: Decoded token identity information.
    """
    logger.info("Protected /me route accessed by user=%s", current_user["email"])
    return schemas.TokenData(email=current_user["email"])


@router.post("/change-password", response_model=schemas.MessageResponse)
async def change_password(
    payload: schemas.ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change the authenticated user's password.

    Args:
        payload: Current and new password.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        MessageResponse: Confirmation message.
    """
    result = await db.execute(
        select(models.User).where(models.User.id == current_user["id"])
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    if not auth_utils.verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    user.password_hash = auth_utils.get_password_hash(payload.new_password)
    try:
        db.add(user)
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("Failed to change password for user_id=%s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update password.",
        ) from exc

    logger.info("Password changed for user_id=%s", user.id)
    return schemas.MessageResponse(message="Password updated successfully.")


@router.post("/forgot-password", response_model=schemas.MessageResponse)
async def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a password-reset flow without revealing whether the email exists.

    When SMTP is configured, emails a one-time reset link. In development
    without SMTP, logs the reset URL for local testing.
    """
    if app_settings.APP_ENV.lower() == "production" and not app_settings.smtp_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is not configured on this server.",
        )

    result = await db.execute(select(models.User).where(models.User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        return schemas.MessageResponse(message=_GENERIC_FORGOT_MESSAGE)

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    reset_row = models.PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_reset_token(raw_token),
        expires_at=now + _RESET_TOKEN_TTL,
        used_at=None,
        created_at=now,
    )
    db.add(reset_row)
    await db.commit()

    reset_url = (
        f"{app_settings.PUBLIC_APP_URL.rstrip('/')}/?reset_token={raw_token}"
    )
    body = (
        "You requested a DocuSage password reset.\n\n"
        f"Open this link within one hour:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    if app_settings.smtp_configured:
        try:
            send_email(
                to_address=user.email,
                subject="DocuSage password reset",
                body=body,
            )
        except EmailDeliveryError as exc:
            logger.error("Forgot-password email failed for user_id=%s: %s", user.id, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send password reset email.",
            ) from exc
    else:
        logger.warning(
            "SMTP not configured; development reset link for user_id=%s: %s",
            user.id,
            reset_url,
        )

    return schemas.MessageResponse(message=_GENERIC_FORGOT_MESSAGE)


@router.post("/reset-password", response_model=schemas.MessageResponse)
async def reset_password(
    payload: schemas.ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Consume a one-time reset token and set a new password.
    """
    token_hash = _hash_reset_token(payload.token)
    result = await db.execute(
        select(models.PasswordResetToken).where(
            models.PasswordResetToken.token_hash == token_hash
        )
    )
    token_row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if token_row is None or token_row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user_result = await db.execute(
        select(models.User).where(models.User.id == token_row.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user.password_hash = auth_utils.get_password_hash(payload.new_password)
    token_row.used_at = now
    try:
        db.add(user)
        db.add(token_row)
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("Reset password commit failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reset password.",
        ) from exc

    logger.info("Password reset completed for user_id=%s", user.id)
    return schemas.MessageResponse(message="Password has been reset. You can log in now.")
