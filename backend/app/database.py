import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings

# Set up logging for the database module
logger = logging.getLogger("database")
logger.setLevel(logging.DEBUG) 

# --- 1. Settings Configuration ---
class Settings(BaseSettings):
    # Reads environment variable DATABASE_URL from docker-compose
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/docu_sage_db"
    
settings = Settings()
logger.info(f"Database settings loaded. URL: {settings.DATABASE_URL.split('@')[-1]}") # Log without credentials

# --- 2. Database Engine and Session Setup ---
try:
    # Use 'asyncpg' driver for asynchronous operations
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    logger.info("SQLAlchemy engine and session maker initialized.")
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize SQLAlchemy engine: {e}")
    # Application should fail fast if the engine cannot be created

# Base class for all models
class Base(DeclarativeBase):
    pass

# Dependency for protected routes
async def get_db():
    """Provides an asynchronous database session, handles closure, and logs errors."""
    session = AsyncSessionLocal()
    logger.debug("New DB session acquired.")
    try:
        yield session
    except Exception as e:
        logger.error(f"Error during database operation within session: {e}")
        # Re-raise the exception after logging to trigger FastAPI's error handling
        raise
    finally:
        # CRITICAL: Ensures session is always closed, regardless of success or failure.
        await session.close()
        logger.debug("DB session closed.")
            
# Function to create tables
async def init_db():
    """Attempts to connect to DB and create tables, handling connection errors."""
    logger.info("Attempting to connect to PostgreSQL and create tables...")
    try:
        # Begin connection
        async with engine.begin() as conn:
            # Create all tables defined by inheriting from Base (only 'User' currently)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully (or already exist).")
    except Exception as e:
        # ERROR HANDLING: This catches failure if the DB container is not ready or connection fails
        logger.critical(f"CRITICAL ERROR: Failed to create database tables. Is DB service running? Details: {e}")
        # NOTE: We allow the app to run, but this error is vital for debugging setup failures.
