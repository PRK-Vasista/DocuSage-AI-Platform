import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import init_db
from .routers import auth # IMPORT NEW ROUTER

# --- Global Logging Configuration ---
# Configure the root logger to output debug messages and format them nicely.
logging.basicConfig(
    level=logging.DEBUG, # Set global level to DEBUG to capture all module logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout # Ensure logs go to standard output (captured by Docker)
)
# Get a specific logger for this module
logger = logging.getLogger("main")

# --- Startup/Shutdown Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup (DB connection/table creation) and shutdown.
    """
    logger.info("Application lifespan start: Initializing services.")
    
    # Database Initialization (Crucial step wrapped in the lifespan context)
    try:
        await init_db()
        logger.info("Database initialization complete.")
    except Exception as e:
        # If DB connection fails, we log critically but allow FastAPI to start for dev/debugging
        logger.critical(f"CRITICAL ERROR: Failed to initialize database during startup. Application may be non-functional. Detail: {e}")

    yield
    
    # Cleanup logic (if any is needed on shutdown)
    logger.info("Application lifespan end: Shutting down.")

# --- FastAPI App Instance ---
app = FastAPI(
    title="DocuSage AI Platform (v1.0 - Auth Ready)",
    description="Backend service with full authentication and robust logging implemented.",
    version="1.0.0",
    lifespan=lifespan
)

# --- START: CORS Configuration to allow frontend requests ---
origins = [
    "http://localhost",
    "http://localhost:3000",  # Your React Frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END: CORS Configuration ---

# --- Include Router ---
logger.info("Including Authentication router...")
app.include_router(auth.router) 
logger.info("Routers successfully included.")

# --- Root Route ---
@app.get("/")
def read_root():
    """Simple root endpoint check."""
    logger.debug("Root endpoint accessed successfully.") 
    return {"message": "DocuSage Backend is Running! Check /docs for API details."}
