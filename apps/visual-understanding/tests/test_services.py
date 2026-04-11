# FILE: apps/visual-understanding/tests/test_services.py
from __future__ import annotations

from PIL import Image
import pytest

from services.layout_classifier import LayoutClassifier
from services.brand_score import BrandConsistencyScorer


@pytest.mark.asyncio
async def test_layout_classifier_step() -> None:
    img = Image.new("RGB", (1024, 768), color=(255, 255, 255))
    layout, conf = await LayoutClassifier().process(img, 0.8)
    assert layout in {"landscape", "portrait", "square"}
    assert 0.0 <= conf <= 1.0


@pytest.mark.asyncio
async def test_brand_score_weights() -> None:
    scorer = BrandConsistencyScorer(0.4, 0.2, 0.2, 0.2)
    score = await scorer.process(1.0, 0.5, 0.5, 0.5)
    assert round(score, 2) == 0.70
