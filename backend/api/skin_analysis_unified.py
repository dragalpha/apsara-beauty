"""
Unified Skin Analysis API - Uses the most powerful model available
Consolidates both heuristic and optimized analyzers with fallback logic
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import hashlib
import numpy as np
from PIL import Image
import logging
import os

from backend.services import image_service
from backend.services.product_service import recommend_products

# Import both analyzers with fallback logic
try:
    from backend.ml_models.optimized_analyzer import get_optimized_analyzer
    _has_optimized = True
    logging.info("Optimized TorchScript analyzer available")
except ImportError:
    _has_optimized = False
    logging.warning("Optimized analyzer not available, using heuristic analyzer only")

from backend.ml_models import analyze_image as heuristic_analyze

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisMode(str, Enum):
    QUICK = "quick"          # Fast heuristic analysis
    DETAILED = "detailed"    # Full optimized analysis (preferred)
    COMPARATIVE = "comparative"  # Both models for comparison


class ConfidenceScore(BaseModel):
    skin_type: float = Field(0.8, ge=0, le=1)
    concerns: Dict[str, float] = Field(default_factory=dict)
    overall: float = Field(0.75, ge=0, le=1)


class ProductItem(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    concerns: List[str]
    rating: Optional[float] = None
    price: Optional[float] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    match_score: float = Field(0.5, ge=0, le=1, description="Match to user needs")


class ImageMetadata(BaseModel):
    width: int
    height: int
    format: str
    size_bytes: int
    hash: str
    quality_score: float = Field(1.0, ge=0, le=1)


class SkinAnalysisResult(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    timestamp: datetime
    skin_type: str
    concerns: List[str]
    confidence_scores: ConfidenceScore
    recommendations: Union[str, Dict[str, Any]]
    image_metadata: ImageMetadata
    products: List[ProductItem] = Field(default_factory=list)
    processing_time_ms: int
    model_used: str = Field(description="Which model was used for analysis")
    previous_analysis_id: Optional[str] = None
    improvement_areas: List[str] = Field(default_factory=list)


def _check_image_quality(file_path: str) -> Dict[str, Any]:
    """Comprehensive image quality assessment"""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            fmt = img.format or "unknown"
            
            # Convert to grayscale for quality metrics
            arr = np.array(img.convert("L"))
            mean_brightness = float(np.mean(arr))
            
            # Quality scoring based on multiple factors
            quality = 1.0
            
            # Resolution check
            if width < 224 or height < 224:
                quality *= 0.4  # Very low resolution
            elif width < 512 or height < 512:
                quality *= 0.7  # Low resolution
            elif width >= 1024 and height >= 1024:
                quality *= 1.1  # High resolution bonus
                
            # Brightness check
            if mean_brightness < 30:
                quality *= 0.3  # Too dark
            elif mean_brightness < 80:
                quality *= 0.6  # Dark
            elif mean_brightness > 220:
                quality *= 0.4  # Too bright/overexposed
            elif mean_brightness > 180:
                quality *= 0.7  # Bright
                
            # Contrast check (using standard deviation)
            contrast = float(np.std(arr))
            if contrast < 20:
                quality *= 0.5  # Very low contrast
            elif contrast < 40:
                quality *= 0.8  # Low contrast
                
            # Generate image hash for deduplication
            img_hash = hashlib.md5(img.tobytes()).hexdigest()
            
        # File size check
        size_bytes = os.path.getsize(file_path)
        if size_bytes < 10000:  # Less than 10KB
            quality *= 0.3
            
        return {
            "width": width,
            "height": height,
            "format": fmt,
            "size_bytes": size_bytes,
            "hash": img_hash,
            "quality_score": max(0.1, min(1.0, quality)),
        }
    except Exception as e:
        logger.error(f"Error checking image quality: {str(e)}")
        return {
            "width": 0, 
            "height": 0, 
            "format": "unknown", 
            "size_bytes": 0, 
            "hash": "", 
            "quality_score": 0.0
        }


def _run_unified_analysis(image_path: str, mode: AnalysisMode) -> Dict[str, Any]:
    """
    Run the most appropriate analysis based on available models and mode
    Priority: Optimized > Heuristic
    """
    model_used = "heuristic"
    
    # Try optimized analyzer first (most powerful)
    if _has_optimized and mode in (AnalysisMode.DETAILED, AnalysisMode.COMPARATIVE):
        try:
            analyzer = get_optimized_analyzer()
            opt_result = analyzer.analyze(image_path)
            
            if opt_result and opt_result.get("skin_type"):
                model_used = "optimized_torchscript"
                logger.info("Using optimized TorchScript model")
                
                return {
                    "skin_type": opt_result.get("skin_type", "Normal"),
                    "concerns": opt_result.get("concerns", ["General"]),
                    "recommendations": opt_result.get("recommendations", "Maintain gentle skincare routine with daily SPF."),
                    "skin_confidence": 0.9,  # Higher confidence for ML model
                    "concern_scores": {c: 0.85 for c in opt_result.get("concerns", [])},
                    "overall_confidence": 0.88,
                    "model_used": model_used,
                }
            else:
                logger.warning("Optimized analyzer returned empty result, falling back")
                
        except Exception as e:
            logger.warning(f"Optimized analyzer failed: {str(e)}. Falling back to heuristic.")
    
    # Fallback to heuristic analyzer
    try:
        model_used = "heuristic_opencv"
        logger.info("Using heuristic OpenCV model")
        
        heuristic_result = heuristic_analyze(image_path)
        
        if heuristic_result and "results" in heuristic_result:
            results = heuristic_result["results"]
            return {
                "skin_type": results.get("skin_type", "Normal"),
                "concerns": results.get("concerns", ["General"]),
                "recommendations": results.get("recommendations", "Maintain gentle skincare routine with daily SPF."),
                "skin_confidence": 0.75,
                "concern_scores": {c: 0.7 for c in results.get("concerns", [])},
                "overall_confidence": 0.72,
                "model_used": model_used,
            }
        else:
            logger.error("Heuristic analyzer returned invalid result")
            
    except Exception as e:
        logger.error(f"Heuristic analyzer failed: {str(e)}")
    
    # Ultimate fallback
    return {
        "skin_type": "Normal",
        "concerns": ["General"],
        "recommendations": "We couldn't analyze your skin in detail. Please try with a clearer photo in good lighting.",
        "skin_confidence": 0.3,
        "concern_scores": {"General": 0.3},
        "overall_confidence": 0.3,
        "model_used": "fallback",
    }


@router.post("/analyze", response_model=SkinAnalysisResult)
async def analyze_skin_unified(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: AnalysisMode = Query(default=AnalysisMode.DETAILED, description="Analysis mode - DETAILED uses the most powerful model"),
    include_products: bool = Query(default=True),
    max_products: int = Query(default=10, ge=1, le=50),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
):
    """
    Unified skin analysis endpoint using the most powerful available model.
    
    - **DETAILED mode**: Uses optimized TorchScript model (recommended)
    - **QUICK mode**: Uses fast heuristic analysis
    - **COMPARATIVE mode**: Uses optimized model with fallback
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Validate input
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided or empty filename")
            
        if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(
                status_code=400, 
                detail="Only JPEG, PNG, and WebP images are supported"
            )

        # Save uploaded file
        image_path = await image_service.save_upload_file(file)
        if not image_path:
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

        # Check image quality
        metadata = _check_image_quality(image_path)
        
        if metadata.get("quality_score", 0) < 0.2:
            raise HTTPException(
                status_code=400, 
                detail="Image quality too low. Please upload a clearer photo with better lighting and higher resolution."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing image upload")

    # Run analysis
    try:
        analysis_result = await asyncio.get_event_loop().run_in_executor(
            None, _run_unified_analysis, image_path, mode
        )
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Skin analysis failed")

    # Create confidence scores
    confidence = ConfidenceScore(
        skin_type=analysis_result.get("skin_confidence", 0.8),
        concerns={c: analysis_result.get("concern_scores", {}).get(c, 0.7) 
                 for c in analysis_result.get("concerns", [])},
        overall=analysis_result.get("overall_confidence", 0.75),
    )

    # Get product recommendations
    products: List[ProductItem] = []
    if include_products:
        try:
            product_recs = recommend_products(analysis_result.get("concerns", []))
            for p in product_recs[:max_products]:
                products.append(
                    ProductItem(
                        id=p.get("id", str(uuid.uuid4())),
                        name=p.get("name", "Product"),
                        brand=p.get("brand", ""),
                        category=p.get("category", ""),
                        concerns=p.get("concerns", []),
                        rating=p.get("rating"),
                        price=p.get("price"),
                        url=p.get("url"),
                        image_url=p.get("image_url"),
                        ingredients=p.get("ingredients", []),
                        match_score=min(0.9, confidence.overall + 0.1),
                    )
                )
        except Exception as e:
            logger.warning(f"Product recommendation failed: {str(e)}")

    # Calculate processing time
    processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)

    return SkinAnalysisResult(
        analysis_id=str(uuid.uuid4()),
        status=AnalysisStatus.COMPLETED,
        timestamp=datetime.utcnow(),
        skin_type=analysis_result.get("skin_type", "Normal"),
        concerns=analysis_result.get("concerns", ["General"]),
        confidence_scores=confidence,
        recommendations=analysis_result.get("recommendations", ""),
        image_metadata=ImageMetadata(**metadata),
        products=products,
        processing_time_ms=processing_time,
        model_used=analysis_result.get("model_used", "unknown"),
    )


@router.get("/health")
async def health_check():
    """Health check endpoint with model availability info"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models_available": {
            "optimized_torchscript": _has_optimized,
            "heuristic_opencv": True,
        },
        "recommended_mode": "detailed" if _has_optimized else "quick"
    }


@router.get("/models/info")
async def model_info():
    """Get information about available analysis models"""
    models = {
        "heuristic_opencv": {
            "available": True,
            "description": "OpenCV-based heuristic analysis with face detection",
            "features": ["Face detection", "HSV analysis", "Texture analysis", "Region-based detection"],
            "speed": "fast",
            "accuracy": "moderate"
        }
    }
    
    if _has_optimized:
        models["optimized_torchscript"] = {
            "available": True,
            "description": "TorchScript deep learning model for advanced skin analysis",
            "features": ["Deep learning", "Multi-class classification", "High accuracy", "Robust to lighting"],
            "speed": "moderate",
            "accuracy": "high"
        }
    else:
        models["optimized_torchscript"] = {
            "available": False,
            "description": "TorchScript model not available (PyTorch not installed or model file missing)",
            "reason": "Missing dependencies or model file"
        }
    
    return {
        "models": models,
        "default_model": "optimized_torchscript" if _has_optimized else "heuristic_opencv",
        "recommendation": "Use DETAILED mode for best results" if _has_optimized else "Use QUICK mode"
    }
