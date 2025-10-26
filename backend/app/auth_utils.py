import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Annotated, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings

# Set up logging for this module
logger = logging.getLogger("auth_utils")
logger.setLevel(logging.DEBUG) # Set to DEBUG for detailed tracking of token lifecycle

# --- Configuration: Reads from environment (docker-compose) ---
class AuthSettings(BaseSettings):
    """Loads environment variables for security configuration."""
    SECRET_KEY: str = "please-change-this-to-a-long-random-string-in-next-sprint" # Default fallback
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 days expiration default
        
auth_settings = AuthSettings()
logger.info("Auth settings loaded successfully.")

# Configuration for Argon2
# Argon2 is the recommended modern hashing scheme and handles long passwords without byte limits.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
logger.debug("Password CryptContext initialized with Argon2.")

# Defines the scheme for expecting an OAuth2 Bearer token in the header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its hash."""
    logger.debug("Attempting password verification.")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password using Argon2., truncating if necessary."""
    # bcrypt has a 72 byte limit on input password length.
    """Hashes a password using Argon2."""
    logger.debug("Password Encrytion Successfull.")
    return pwd_context.hash(password)

# --- JWT Token Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token.
    Includes exception handling for token generation failure.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # CRITICAL EXCEPTION HANDLING for token encoding
    try:
        encoded_jwt = jwt.encode(to_encode, auth_settings.SECRET_KEY, algorithm=auth_settings.ALGORITHM)
        logger.debug(f"JWT token successfully created. Expires: {expire}")
        return encoded_jwt
    except Exception as e:
        logger.critical(f"FATAL: Error creating JWT token. Check SECRET_KEY or ALGORITHM settings. Error: {e}")
        # Raise an internal server error if the security mechanism fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security mechanism failed. Cannot issue token."
        )

# --- Dependency for Protected Routes (Authentication) ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Validates a JWT and extracts the user's identifier ('sub').
    This function is run before protected endpoint logic.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Token is invalid or expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # EXCEPTION HANDLING for token decoding and validation
    try:
        # Decode the token using the application's secret key
        payload = jwt.decode(token, auth_settings.SECRET_KEY, algorithms=[auth_settings.ALGORITHM])
        email: str = payload.get("sub")
        
        # Check if the required claim ('sub') is present
        if email is None:
            logger.warning("Token decoded successfully, but 'sub' (email) claim was missing.")
            raise credentials_exception
            
    except JWTError as e:
        # Handle specific JWT errors (e.g., signature mismatch, token expired)
        logger.warning(f"JWT Validation Failed. Type: {e.__class__.__name__}, Detail: {e}")
        raise credentials_exception
    except Exception as e:
        # Handle unexpected errors during token processing
        logger.error(f"Unexpected error during token processing: {e}")
        raise credentials_exception
    
    logger.info(f"Token successfully validated for user: {email}")
    # Returns the email, which can be used by the endpoint to fetch user data
    return {"email": email} 
