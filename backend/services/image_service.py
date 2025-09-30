# backend/services/image_service.py
# ---
# This service handles saving uploaded images.
# We've modified it to save files to the local server instead of AWS S3.

import os
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

# Create the uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def save_upload_file(file: UploadFile) -> str:
    """
    Saves an uploaded file to the local filesystem and returns the file path.
    """
    # Basic validation for file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    # Generate a unique filename to prevent overwriting
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # Asynchronously write the file content
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        # Handle potential file writing errors
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Return the path that will be used to access the file
    # e.g., "uploads/some-unique-name.jpg"
    return str(file_path)