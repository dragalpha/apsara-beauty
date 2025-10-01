"""
Optimized skin analyzer wrapper.

This module attempts to use a tiny TorchScript model if available and
PyTorch is installed. If not, callers should gracefully fall back to
the heuristic analyzer in skin_analyzer.py.
"""

from typing import Any, Dict, List
import os
import logging

logger = logging.getLogger(__name__)


class OptimizedSkinAnalyzer:
    def __init__(self, model_path: str = "backend/models/tiny_model_scripted.pt") -> None:
        self.model_path = model_path
        self.device = None
        self.model = None
        self._loaded = False

    def _lazy_load(self) -> None:
        if self._loaded:
            return
        try:
            import torch  # type: ignore

            self.torch = torch
            self.device = torch.device("cpu")
            self.model = torch.jit.load(self.model_path, map_location=self.device)
            self.model.eval()
            # Warmup
            with torch.no_grad():
                _ = self.model(torch.randn(1, 3, 128, 128))
            self._loaded = True
            logger.info("Loaded TorchScript model: %s", self.model_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Torch model unavailable (%s). Falling back.", exc)
            raise

    def _preprocess(self, image_path: str):
        from PIL import Image
        import numpy as np

        img = Image.open(image_path).convert("RGB").resize((128, 128))
        arr = (np.array(img).astype("float32") / 255.0)
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        for i in range(3):
            arr[:, :, i] = (arr[:, :, i] - mean[i]) / std[i]
        chw = arr.transpose(2, 0, 1)
        x = self.torch.from_numpy(chw).unsqueeze(0)
        return x

    def analyze(self, image_path: str) -> Dict[str, Any]:
        self._lazy_load()
        with self.torch.no_grad():
            x = self._preprocess(image_path)
            out = self.model(x)
            # Expected keys: 'skin_type' (softmax), 'concerns' (sigmoid)
            skin_probs = out["skin_type"].cpu().numpy()[0]
            concern_probs = out["concerns"].cpu().numpy()[0]
        skin_types = ["normal", "oily", "dry", "combination"]
        concerns_list = ["acne", "wrinkles", "dark_spots", "redness", "pores", "sensitivity"]

        import numpy as np

        st_idx = int(np.argmax(skin_probs))
        skin_type = skin_types[st_idx].capitalize()

        idxs = np.where(concern_probs > 0.3)[0]
        if len(idxs) == 0:
            idxs = np.argsort(concern_probs)[-2:]
        concerns = [concerns_list[int(i)].replace("_", " ").title() for i in idxs]

        # Simple recommendations
        base_rec = {
            "Oily": "Use oil-free moisturizer and niacinamide.",
            "Dry": "Use hyaluronic acid and ceramide-rich creams.",
            "Combination": "Target T-zone with lightweight products; hydrate dry areas.",
            "Normal": "Maintain gentle routine with daily SPF.",
        }.get(skin_type, "Maintain gentle routine with daily SPF.")

        return {
            "skin_type": skin_type,
            "concerns": concerns or ["General"],
            "recommendations": base_rec,
        }


_singleton: OptimizedSkinAnalyzer | None = None


def get_optimized_analyzer() -> OptimizedSkinAnalyzer:
    global _singleton
    if _singleton is None:
        _singleton = OptimizedSkinAnalyzer(
            model_path=os.getenv("TINY_MODEL_PATH", "backend/models/tiny_model_scripted.pt")
        )
    return _singleton


