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

from services import image_service
from services.product_service import recommend_products
from ml_models import analyze_image as heuristic_analyze

try:
    from ml_models.optimized_analyzer import get_optimized_analyzer
    _has_optimized = True
except ImportError:
    _has_optimized = False
    import logging
    logging.warning("Optimized analyzer not available, falling back to heuristic analyzer")


router = APIRouter()


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisMode(str, Enum):
    QUICK = "quick"
    DETAILED = "detailed"
    COMPARATIVE = "comparative"


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


class SkinAnalysisRequest(BaseModel):
    mode: AnalysisMode = AnalysisMode.DETAILED
    include_products: bool = True
    max_products: int = Field(default=10, ge=1, le=50)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


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
    previous_analysis_id: Optional[str] = None
    improvement_areas: List[str] = Field(default_factory=list)


def _check_quality(file_path: str) -> Dict[str, Any]:
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            fmt = img.format or "unknown"
            arr = np.array(img.convert("L"))
            mean_brightness = float(np.mean(arr))
            quality = 1.0
            if width < 224 or height < 224:
                quality *= 0.5
            elif width < 512 or height < 512:
                quality *= 0.8
            if mean_brightness < 50 or mean_brightness > 200:
                quality *= 0.8
            img_hash = hashlib.md5(img.tobytes()).hexdigest()
        import os
        size_bytes = os.path.getsize(file_path)
        return {
            "width": width,
            "height": height,
            "format": fmt,
            "size_bytes": size_bytes,
            "hash": img_hash,
            "quality_score": max(0.1, min(1.0, quality)),
        }
    except Exception:
        return {"width": 0, "height": 0, "format": "unknown", "size_bytes": 0, "hash": "", "quality_score": 0.0}


def _run_models(image_path: str, mode: AnalysisMode) -> Dict[str, Any]:
    # Try optimized analyzer first if available
    if _has_optimized and mode in (AnalysisMode.QUICK, AnalysisMode.DETAILED):
        try:
            analyzer = get_optimized_analyzer()
            opt = analyzer.analyze(image_path)
            if not opt:
                logger.warning("Optimized analyzer returned empty result")
                raise ValueError("Empty result from optimized analyzer")
                
            return {
                "skin_type": opt.get("skin_type", "Normal"),
                "concerns": opt.get("concerns", ["General"]),
                "recommendations": opt.get("recommendations", "Maintain gentle routine with SPF."),
                "skin_confidence": 0.85,
                "concern_scores": {c: 0.7 for c in opt.get("concerns", [])},
                "overall_confidence": 0.8,
            }
        except Exception as e:
            logger.warning(f"Optimized analyzer failed: {str(e)}. Falling back to heuristic.")
    
    # Fallback to heuristic analyzer
    try:
        res = heuristic_analyze(image_path)
        if not res or "results" not in res:
            logger.error("Heuristic analyzer returned invalid result")
            return {
                "skin_type": "Normal",
                "concerns": ["General"],
                "recommendations": "We couldn't analyze your skin in detail. Please try with a clearer photo in good lighting.",
                "skin_confidence": 0.5,
                "concern_scores": {"General": 0.5},
                "overall_confidence": 0.5,
            }
            
        return {
            "skin_type": res["results"].get("skin_type", "Normal"),
            "concerns": res["results"].get("concerns", ["General"]),
            "recommendations": res["results"].get("recommendations", "Maintain gentle skincare routine with SPF."),
            "skin_confidence": 0.75,
            "concern_scores": {c: 0.6 for c in res["results"].get("concerns", [])},
            "overall_confidence": 0.7,
        }
    except Exception as e:
        logger.error(f"All skin analysis methods failed: {str(e)}")
        return {
            "skin_type": "Unknown",
            "concerns": ["General"],
            "recommendations": "We encountered an error analyzing your skin. Please try again with a different photo.",
            "skin_confidence": 0.3,
            "concern_scores": {"General": 0.3},
            "overall_confidence": 0.3,
        }


@router.post("/analyze/v2", response_model=SkinAnalysisResult)
async def analyze_v2(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: AnalysisMode = Query(default=AnalysisMode.DETAILED),
    include_products: bool = Query(default=True),
    max_products: int = Query(default=10, ge=1, le=50),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
):
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided or empty filename")
            
        if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Only JPEG/PNG/WebP supported")

        image_path = await image_service.save_upload_file(file)
        if not image_path:
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

        start = asyncio.get_event_loop().time()
        meta = _check_quality(image_path)
        
        if meta.get("quality_score", 0) < 0.3:
            raise HTTPException(status_code=400, detail="Image quality too low. Please upload a clearer photo with better lighting and resolution.")
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing image upload")

    ml = await asyncio.get_event_loop().run_in_executor(None, _run_models, image_path, mode)

    conf = ConfidenceScore(
        skin_type=ml.get("skin_confidence", 0.8),
        concerns={c: ml.get("concern_scores", {}).get(c, 0.7) for c in ml.get("concerns", [])},
        overall=ml.get("overall_confidence", 0.75),
    )

    products: List[ProductItem] = []
    if include_products:
        recs = recommend_products(ml.get("concerns", []))
        for p in recs[:max_products]:
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
                    match_score=0.5,
                )
            )

    elapsed = int((asyncio.get_event_loop().time() - start) * 1000)

    return SkinAnalysisResult(
        analysis_id=str(uuid.uuid4()),
        status=AnalysisStatus.COMPLETED,
        timestamp=datetime.utcnow(),
        skin_type=ml.get("skin_type", "Normal"),
        concerns=ml.get("concerns", ["General"]),
        confidence_scores=conf,
        recommendations=ml.get("recommendations", ""),
        image_metadata=ImageMetadata(**meta),
        products=products,
        processing_time_ms=elapsed,
    )


@router.get("/analyze/v2/health")
async def health_v2():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


