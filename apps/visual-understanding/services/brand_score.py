# FILE: apps/visual-understanding/services/brand_score.py
from __future__ import annotations


class BrandConsistencyScorer:
    def __init__(self, color_weight: float, typography_weight: float, layout_weight: float, logo_weight: float) -> None:
        self.color_weight = color_weight
        self.typography_weight = typography_weight
        self.layout_weight = layout_weight
        self.logo_weight = logo_weight

    async def process(
        self,
        color_alignment: float,
        typography_alignment: float,
        layout_alignment: float,
        logo_alignment: float,
    ) -> float:
        """Compute weighted brand consistency using required alignment weights."""
        score = (
            self.color_weight * color_alignment
            + self.typography_weight * typography_alignment
            + self.layout_weight * layout_alignment
            + self.logo_weight * logo_alignment
        )
        return max(0.0, min(1.0, score))
