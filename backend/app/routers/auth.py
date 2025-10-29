import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
# The core JWT imports are now handled via auth_utils functions, 
# but we need JWTError for the custom get_current_user check.
from jose import JWTError 

# Local imports
from .. import schemas, models, auth_utils
from ..database import get_db
from ..auth_utils import get_password_hash, verify_password, create_access_token, get_current_user

# Set up a dedicated logger for the Auth Router
# FIX APPLIED: Prefix removed to prevent double-prefixing with main.py
router = APIRouter(tags=["Auth"])
logger = logging.getLogger("auth_router")
logger.setLevel(logging.INFO) # Use INFO for operational logs, DEBUG for internal flows

# --- Security Dependency ---
# NOTE: This implementation of get_current_user is custom and relies on the user object,
# whereas the one in auth_utils.py is for token validation only.
async def get_current_user(token: str = Depends(auth_utils.oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Dependency function to verify JWT token and retrieve the user object.
    Raises HTTPException 401 if token is invalid or user not found.
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    validated_email = None

    # 1. Use the token validation logic from auth_utils
    try:
        # get_current_user in auth_utils returns {'email': email} if token is valid
        # This part handles decoding and expiration check
        token_data_dict = await auth_utils.get_current_user(token) 
        validated_email = token_data_dict.get("email")
        
        if validated_email is None:
            logger.warning("Token valid but 'email' (sub) claim missing.")
            raise credentials_exception
            
    except HTTPException:
        # Re-raise the 401 exception if validation fails in auth_utils
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token processing: {e}")
        raise credentials_exception

    # 4. Fetch the user from the database using the extracted email string
    try:
        stmt = select(models.User).where(models.User.email == validated_email) # Use the validated_email string
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"DB ERROR: Query failed during user lookup for validated token. Detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user lookup for authenticated request."
        )
    
    if user is None:
        logger.warning(f"Authenticated user not found in DB: {validated_email}")
        raise credentials_exception
    
    # 5. Return the full user object (in a dict format for dependency use)
    return {'email': user.email, 'id': user.id}

@router.post("/register", response_model=schemas.Token)
async def register_user(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Handles new user registration, hashes password, and issues a JWT.
    Includes robust checks for existing user and database commit failure.
    """
    
    logger.info(f"REGISTRATION ATTEMPT: Checking existing user for email: {user_data.email}")
    
    # 1. Check if user already exists
    try:
        stmt = select(models.User).where(models.User.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        # Log specific DB execution errors
        logger.error(f"DB ERROR: Query failed during registration check for {user_data.email}. Detail: {e.__class__.__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user existence check. See backend logs."
        )

    if existing_user:
        logger.warning(f"REGISTRATION FAILED: Email already registered: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # 2. Hash password and create user object
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(email=user_data.email, password_hash=hashed_password)
    
    # 3. Commit user to database (CRITICAL SECTION)
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"REGISTRATION SUCCESS: User created. ID: {new_user.id}, Email: {new_user.email}")
    except SQLAlchemyError as e:
        # Ensure transaction is rolled back and log a critical failure
        await db.rollback()
        logger.critical(f"DB CRITICAL: Failed to commit new user {user_data.email} to DB. Rollback initiated. Detail: {e.__class__.__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to a critical database error."
        )

    # 4. Create and return JWT
    access_token = create_access_token(data={"sub": new_user.email})
    return schemas.Token(access_token=access_token)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Handles user login, verifies credentials, and issues a JWT.
    """
    
    logger.info(f"LOGIN ATTEMPT: Initiated for email: {user_data.email}")

    # 1. Find user by email
    try:
        stmt = select(models.User).where(models.User.email == user_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"DB ERROR: Query failed during login attempt for {user_data.email}. Detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user lookup. See backend logs."
        )

    # 2. Verify existence
    if not user:
        logger.warning(f"LOGIN FAILED: User not found for email: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Verify password
    if not verify_password(user_data.password, user.password_hash):
        logger.warning(f"LOGIN FAILED: Password mismatch for user ID {user.id}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Create and return JWT
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"LOGIN SUCCESS: User authenticated: {user.email}")
    return schemas.Token(access_token=access_token)

# --- EXAMPLE PROTECTED ROUTE (for testing the get_current_user dependency) ---
@router.get("/me", response_model=schemas.TokenData)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the current user's email, proving the JWT is valid.
    """
    logger.info(f"Protected route accessed by user: {current_user['email']}")
    # current_user is the dictionary returned by get_current_user
    return schemas.TokenData(email=current_user['email'])
