from typing import Dict, List, Tuple
import uuid
import cv2
import numpy as np


def _detect_face_roi_bgr(image_bgr: np.ndarray) -> Tuple[int, int, int, int]:
    """
    Detect a face using OpenCV Haar cascades and return (x, y, w, h).
    Falls back to center crop if no face is detected.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) > 0:
        # Pick the largest detected face
        faces_sorted = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)
        x, y, w, h = faces_sorted[0]
        return int(x), int(y), int(w), int(h)
    # Fallback: center crop square
    h_img, w_img = image_bgr.shape[:2]
    side = int(min(h_img, w_img) * 0.6)
    cx, cy = w_img // 2, h_img // 2
    x = max(0, cx - side // 2)
    y = max(0, cy - side // 2)
    return x, y, side, side


def _compute_skin_metrics(face_bgr: np.ndarray) -> Dict[str, float]:
    """
    Compute basic metrics from face ROI:
    - brightness_mean: mean V channel in HSV (0-255)
    - saturation_mean: mean S channel in HSV (0-255)
    - highlight_ratio: fraction of pixels with V>200 and S<40 (specular highlights)
    - texture_var: variance of Laplacian (focus/texture proxy)
    """
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    brightness_mean = float(np.mean(v))
    saturation_mean = float(np.mean(s))
    highlights = (v > 200) & (s < 40)
    highlight_ratio = float(np.mean(highlights.astype(np.float32)))
    lap = cv2.Laplacian(cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F)
    texture_var = float(lap.var())
    return {
        "brightness_mean": brightness_mean,
        "saturation_mean": saturation_mean,
        "highlight_ratio": highlight_ratio,
        "texture_var": texture_var,
    }


def _classify_skin_type(metrics: Dict[str, float]) -> Tuple[str, List[str], str]:
    """
    Heuristic classification based on simple thresholds.
    Returns (skin_type, concerns, recommendation_text).
    """
    b = metrics["brightness_mean"]
    s = metrics["saturation_mean"]
    hi = metrics["highlight_ratio"]
    tv = metrics["texture_var"]

    concerns: List[str] = []

    # Heuristics
    is_oily = hi > 0.05 and b > 140
    is_dry = (b < 110 and s < 60) or tv > 500.0

    if is_oily and is_dry:
        skin_type = "Combination"
        concerns.extend(["Shine", "Dehydration"])
        rec = "Use gentle foaming cleanser, hydrating serum, and non-comedogenic moisturizer."
    elif is_oily:
        skin_type = "Oily"
        concerns.append("Shine")
        rec = "Use salicylic acid cleanser, niacinamide serum, and oil-free moisturizer."
    elif is_dry:
        skin_type = "Dry"
        concerns.append("Dehydration")
        rec = "Use creamy cleanser, hyaluronic acid + ceramides, and richer moisturizer."
    else:
        skin_type = "Normal"
        rec = "Maintain gentle cleanse, light moisturizer, and daily SPF."

    # Additional concern: texture
    if tv > 1200:
        concerns.append("Texture")

    return skin_type, concerns, rec


def analyze_image(image_path: str) -> Dict:
    """
    OpenCV-based heuristic analysis.
    1) Detect face ROI (Haar cascades)
    2) Compute simple metrics (HSV brightness/saturation, specular highlights, texture)
    3) Classify Oily/Dry/Normal/Combination
    """
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        # Fallback result
        return {
            "analysis_id": str(uuid.uuid4()),
            "results": {
                "skin_type": "Unknown",
                "concerns": ["ImageReadError"],
                "recommendations": "Please upload a clear face photo.",
            },
        }

    x, y, w, h = _detect_face_roi_bgr(image_bgr)
    x2, y2 = x + w, y + h
    face_bgr = image_bgr[y:y2, x:x2].copy()
    if face_bgr.size == 0:
        face_bgr = image_bgr

    metrics = _compute_skin_metrics(face_bgr)
    skin_type, concerns, rec = _classify_skin_type(metrics)

    # Ensure concerns non-empty for downstream recs
    if not concerns:
        concerns = ["General"]

    return {
        "analysis_id": str(uuid.uuid4()),
        "results": {
            "skin_type": skin_type,
            "concerns": concerns,
            "recommendations": rec,
        },
    }



