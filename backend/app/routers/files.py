import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from ..routers.auth import get_current_user
from .. import models

# --- Global Logging Configuration ---
logger = logging.getLogger("files_router")

# --- Configuration ---
# Define the root directory for saving files. 
# We'll map this to a Docker Volume later for persistence.
UPLOAD_DIR = "user_uploads"

# Create the upload directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(exist_ok=True)
logger.info(f"File upload directory created/verified: {UPLOAD_DIR}")

# --- Router Setup ---
router = APIRouter(
    prefix="/files",
    tags=["Files"],
)

# --- Endpoint: Secure File Upload ---

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """
    Accepts a single file upload from an authenticated user.
    Saves the file to a unique path based on the user's ID.
    """
    
    # 1. Validation Check: Ensure file type is acceptable
    if file.content_type not in ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        logger.warning(f"Upload rejected: Invalid file type {file.content_type} from user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only PDF, TXT, or DOCX are allowed."
        )

    # 2. Define secure, unique storage path
    # We create a nested directory structure for security and organization:
    # UPLOAD_DIR / user_id / filename
    
    user_dir = Path(UPLOAD_DIR) / str(current_user.id)
    user_dir.mkdir(exist_ok=True) # Ensure the user's personal folder exists
    
    # Sanitize filename to prevent directory traversal attacks (optional but good practice)
    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    file_path = user_dir / safe_filename
    
    logger.info(f"Receiving file '{file.filename}' for user {current_user.email} (ID: {current_user.id}).")

    # 3. Save the file synchronously to disk
    try:
        # FastAPI's UploadFile reads the file in chunks and saves it
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File saved successfully to: {file_path}")

        # 4. Respond to the client
        return {
            "message": "File uploaded successfully",
            "filename": safe_filename,
            "path": str(file_path),
            "user_id": current_user.id
        }

    except Exception as e:
        logger.error(f"Error saving file for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file on the server."
        )
    finally:
        # Important: Close the file handler
        await file.close()
