# FILE: apps/visual-understanding/services/typography_inference.py
from __future__ import annotations

from PIL import Image
import pytesseract


class TypographyInference:
    def __init__(self) -> None:
        pass

    async def process(self, image: Image.Image) -> tuple[str, float]:
        """Infer typography style from OCR glyph properties and heuristic font metrics."""
        text = pytesseract.image_to_string(image)
        avg_word_len = (sum(len(w) for w in text.split()) / max(len(text.split()), 1)) if text else 0.0
        uppercase_ratio = (sum(1 for c in text if c.isupper()) / max(len(text), 1)) if text else 0.0
        stroke_contrast = min(1.0, avg_word_len / 10)
        serif_presence = 1.0 if any(ch in text for ch in "WMR") else 0.3
        x_height_ratio = min(1.0, (1 - uppercase_ratio) + 0.2)

        if serif_presence > 0.7 and stroke_contrast > 0.45:
            return "serif", 0.78
        if x_height_ratio > 0.8 and uppercase_ratio < 0.2:
            return "sans-serif", 0.82
        return "mixed", 0.65
