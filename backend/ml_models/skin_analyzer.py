from pathlib import Path
from typing import Dict, List


def analyze_image(image_path: str) -> Dict:
    """
    Placeholder analysis using simple heuristics.
    Replace with TensorFlow + MTCNN pipeline in production.
    """
    # Basic shape of the response that API expects
    return {
        "analysis_id": "mock_id_placeholder",
        "results": {
            "skin_type": "Combination",
            "concerns": ["Acne", "Dehydration"],
            "recommendations": "Use a gentle cleanser and a non-comedogenic moisturizer.",
        },
    }



