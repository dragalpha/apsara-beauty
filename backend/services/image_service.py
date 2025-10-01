# backend/services/image_service.py
# ---
# This service handles saving uploaded images.
# We've modified it to save files to the local server instead of AWS S3.

import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from pathlib import Path

# Use environment variable for upload directory, with a local fallback
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_image(file: UploadFile) -> None:
    """
    Validates the uploaded image for type, extension, and size.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    await file.seek(0)  # Reset file pointer

async def save_upload_file(file: UploadFile) -> str:
    """
    Saves an uploaded file to the local filesystem and returns the file path.
    """
    UPLOAD_DIR.mkdir(exist_ok=True)
    await validate_image(file)
    
    # Generate a unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    file_path = UPLOAD_DIR / unique_filename
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Return the relative path that can be used in a URL
    # e.g., "uploads/some-unique-name.jpg"
    return str(file_path).replace('\\', '/')