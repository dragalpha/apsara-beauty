# backend/api/skin_analysis.py
# ---
# This file defines the API endpoint for skin analysis.
# It now uses our local `image_service` to handle the file upload.

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
# Use absolute imports from project root per requirements
from backend.services import image_service
from backend.ml_models import analyze_image
try:
    from backend.ml_models.optimized_analyzer import get_optimized_analyzer
    _has_optimized = True
except Exception:
    _has_optimized = False
from backend.services.product_service import recommend_products


# We'll imagine the ML model service exists like this:
# from ..ml_models import skin_analyzer 

router = APIRouter()

# A mock function to simulate the ML analysis
def mock_skin_analyzer(image_path: str):
    # Temporary shim to call the placeholder model
    return analyze_image(image_path)

# Response models
class ProductItem(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    concerns: List[str]
    url: Optional[str] = None
    image_url: Optional[str] = None


class SkinAnalysisResult(BaseModel):
    analysis_id: str
    skin_type: str
    concerns: List[str]
    recommendations: str
    image_path: str
    products: List[ProductItem] = []


@router.post("/analyze", response_model=SkinAnalysisResult)
async def analyze_skin(
    file: UploadFile = File(...),
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
        if _has_optimized:
            try:
                analyzer = get_optimized_analyzer()
                opt = analyzer.analyze(image_path)
                analysis_results = {
                    "analysis_id": "opt_id",
                    "results": {
                        "skin_type": opt["skin_type"],
                        "concerns": opt["concerns"],
                        "recommendations": opt["recommendations"],
                    },
                }
            except Exception:
                analysis_results = mock_skin_analyzer(image_path)
        else:
            analysis_results = mock_skin_analyzer(image_path)
        user_concerns = analysis_results["results"]["concerns"]

        # Recommend products
        products = recommend_products(user_concerns)
        
        # You might want to include the image URL in the response
        # The URL will depend on your backend's live URL
        # e.g., f"https://your-backend-url.com/{image_path}"
        
        return SkinAnalysisResult(
            analysis_id=analysis_results["analysis_id"],
            skin_type=analysis_results["results"]["skin_type"],
            concerns=analysis_results["results"]["concerns"],
            recommendations=analysis_results["results"]["recommendations"],
            image_path=image_path,
            products=products,
        )
    except HTTPException as he:
        # Propagate known validation errors (e.g., file too large, invalid type)
        raise he
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process image"
        )