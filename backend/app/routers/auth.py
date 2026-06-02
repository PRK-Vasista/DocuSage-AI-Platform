"""
Authentication API routes for DocuSage.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import auth_utils, models, schemas
from ..database import get_db
from ..dependencies.auth import AuthenticatedUser, get_current_user

router = APIRouter(tags=["Auth"])
logger = logging.getLogger("auth_router")
logger.setLevel(logging.INFO)


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
