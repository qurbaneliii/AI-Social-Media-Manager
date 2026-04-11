# FILE: apps/visual-understanding/services/layout_classifier.py
from __future__ import annotations

import numpy as np
from PIL import Image


class LayoutClassifier:
    def __init__(self) -> None:
        pass

    async def process(self, image: Image.Image, style_similarity: float) -> tuple[str, float]:
        """Blend rule-based layout signal with style similarity for final layout confidence."""
        arr = np.array(image)
        h, w, _ = arr.shape
        ratio = w / max(h, 1)

        if ratio > 1.3:
            rule_layout, rule_score = "landscape", 0.75
        elif ratio < 0.8:
            rule_layout, rule_score = "portrait", 0.75
        else:
            rule_layout, rule_score = "square", 0.72

        blended = 0.6 * rule_score + 0.4 * style_similarity
        return rule_layout, max(0.0, min(1.0, blended))
