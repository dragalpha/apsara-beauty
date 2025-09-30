# backend/api/skin_analysis.py
# ---
# This file defines the API endpoint for skin analysis.
# It now uses our local `image_service` to handle the file upload.

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from ..services import image_service
from ..database.connection import get_db

# We'll imagine the ML model service exists like this:
# from ..ml_models import skin_analyzer 

router = APIRouter()

# A mock function to simulate the ML analysis
def mock_skin_analyzer(image_path: str):
    # In a real app, this would load the image and run the ML model
    print(f"Analyzing image at: {image_path}")
    return {
        "analysis_id": "mock_id_12345",
        "results": {
            "skin_type": "Combination",
            "concerns": ["Acne", "Dehydration"],
            "recommendations": "Use a gentle cleanser and a non-comedogenic moisturizer."
        }
    }

# Response models
class SkinAnalysisResult(BaseModel):
    analysis_id: str
    skin_type: str
    concerns: List[str]
    recommendations: str
    image_path: str


@router.post("/analyze", response_model=SkinAnalysisResult)
async def analyze_skin(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """
    Endpoint to upload a skin photo for analysis.
    1. Saves the image using the image_service.
    2. (Simulates) Runs the ML model on the saved image.
    3. Returns the analysis results.
    """
    try:
        # Save the file locally using our new service
        image_path = await image_service.save_upload_file(file)

        # --- ML Model Integration ---
        # Here, you would pass the `image_path` to your ML model
        # For now, we'll use a mock function to simulate the analysis
        analysis_results = mock_skin_analyzer(image_path)
        
        # You might want to include the image URL in the response
        # The URL will depend on your backend's live URL
        # e.g., f"https://your-backend-url.com/{image_path}"
        
        return SkinAnalysisResult(
            analysis_id=analysis_results["analysis_id"],
            skin_type=analysis_results["results"]["skin_type"],
            concerns=analysis_results["results"]["concerns"],
            recommendations=analysis_results["results"]["recommendations"],
            image_path=image_path
        )
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process image"
        )