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


def _normalize_illumination_bgr(face_bgr: np.ndarray) -> np.ndarray:
    """
    Normalize illumination via CLAHE on the V channel in HSV to reduce lighting variance.
    """
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    v_eq = clahe.apply(v)
    hsv_eq = cv2.merge([h, s, v_eq])
    return cv2.cvtColor(hsv_eq, cv2.COLOR_HSV2BGR)


def _compute_skin_mask(face_bgr: np.ndarray) -> np.ndarray:
    """
    Rough skin mask in HSV to exclude background/hair.
    Returns boolean mask (True for skin-like pixels).
    """
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    # Broad skin range in HSV (tuned for diverse tones)
    lower = np.array([0, 20, 40], dtype=np.uint8)
    upper = np.array([25, 255, 255], dtype=np.uint8)
    mask1 = cv2.inRange(hsv, lower, upper)
    # Include some higher H for varied lighting
    lower2 = np.array([160, 15, 30], dtype=np.uint8)
    upper2 = np.array([179, 255, 255], dtype=np.uint8)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)
    # Morphological clean-up
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask.astype(bool)


def _compute_skin_metrics(face_bgr: np.ndarray) -> Dict[str, float]:
    """
    Compute basic metrics from face ROI:
    - brightness_mean: mean V channel in HSV (0-255)
    - saturation_mean: mean S channel in HSV (0-255)
    - highlight_ratio: fraction of pixels with V>200 and S<40 (specular highlights)
    - texture_var: variance of Laplacian (focus/texture proxy)
    """
    # Illumination normalization first
    face_bgr = _normalize_illumination_bgr(face_bgr)
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # Skin mask to focus metrics
    skin_mask = _compute_skin_mask(face_bgr)
    valid = np.count_nonzero(skin_mask)
    if valid < 50:  # if mask fails, fall back to full ROI
        skin_mask = np.ones_like(v, dtype=bool)

    brightness_mean = float(np.mean(v[skin_mask]))
    saturation_mean = float(np.mean(s[skin_mask]))
    highlights = (v > 200) & (s < 40) & skin_mask
    highlight_ratio = float(np.mean(highlights.astype(np.float32)))
    lap = cv2.Laplacian(cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F)
    texture_var = float(lap[skin_mask].var() if skin_mask.any() else lap.var())
    return {
        "brightness_mean": brightness_mean,
        "saturation_mean": saturation_mean,
        "highlight_ratio": highlight_ratio,
        "texture_var": texture_var,
    }


def _compute_region_metrics(face_bgr: np.ndarray) -> Dict[str, float]:
    """
    Region-wise metrics to better detect combination skin.
    Defines simple regions: central T-zone and cheeks.
    Returns highlight ratios per region.
    """
    h_img, w_img = face_bgr.shape[:2]
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    _, s, v = cv2.split(hsv)
    skin_mask = _compute_skin_mask(face_bgr)

    # T-zone: vertical central band and horizontal across center
    x1 = int(w_img * 0.38)
    x2 = int(w_img * 0.62)
    y1 = int(h_img * 0.15)
    y2 = int(h_img * 0.80)
    tzone_mask = np.zeros((h_img, w_img), dtype=bool)
    tzone_mask[y1:y2, x1:x2] = True
    tzone_mask &= skin_mask

    # Cheeks: left and right rectangles
    cy1 = int(h_img * 0.35)
    cy2 = int(h_img * 0.80)
    lx1, lx2 = int(w_img * 0.10), int(w_img * 0.30)
    rx1, rx2 = int(w_img * 0.70), int(w_img * 0.90)
    left_mask = np.zeros((h_img, w_img), dtype=bool)
    left_mask[cy1:cy2, lx1:lx2] = True
    right_mask = np.zeros((h_img, w_img), dtype=bool)
    right_mask[cy1:cy2, rx1:rx2] = True
    left_mask &= skin_mask
    right_mask &= skin_mask

    highlights = (v > 200) & (s < 40)
    def ratio(m: np.ndarray) -> float:
        denom = float(np.count_nonzero(m))
        if denom < 50:
            return 0.0
        return float(np.count_nonzero(highlights & m) / denom)

    return {
        "tzone_highlight_ratio": ratio(tzone_mask),
        "cheek_highlight_ratio": (ratio(left_mask) + ratio(right_mask)) / 2.0,
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
    # Region cues
    region = _compute_region_metrics(metrics.get("face_bgr") if False else None)  # placeholder to keep signature
    # Note: we recompute region metrics below where face_bgr is available in analyze.
    is_oily = hi > 0.05 and b > 135
    is_dry = (b < 110 and s < 60) or tv > 700.0

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
    # Also compute region metrics for combination detection
    region = _compute_region_metrics(face_bgr)
    # Inject region metrics into metrics dict for classification tuning if needed
    metrics.update(region)
    # Adjust classification with region-aware logic
    b = metrics["brightness_mean"]
    s = metrics["saturation_mean"]
    hi = metrics["highlight_ratio"]
    tv = metrics["texture_var"]
    t_hi = metrics.get("tzone_highlight_ratio", 0.0)
    c_hi = metrics.get("cheek_highlight_ratio", 0.0)

    concerns: List[str] = []
    if t_hi - c_hi > 0.06 and b > 135:
        skin_type = "Combination"
        concerns.extend(["Shine"])
        rec = "Mattify T‑zone; hydrate cheeks with ceramides."
    else:
        # Fallback to global heuristics
        is_oily = hi > 0.05 and b > 135
        is_dry = (b < 110 and s < 60) or tv > 700.0
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

    if tv > 1200:
        concerns.append("Texture")

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



