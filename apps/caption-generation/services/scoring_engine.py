# FILE: apps/caption-generation/services/scoring_engine.py
from __future__ import annotations

from config import Settings


class CaptionScoringEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def process(self, variant: dict) -> dict:
        """Compute weighted final score using required caption ranking weights."""
        engagement_predicted = float(variant.get("engagement_predicted", 0.5))
        tone_match = float(variant.get("tone_match", 0.5))
        cta_present = 1.0 if bool(variant.get("cta_present", False)) else 0.0
        keyword_inclusion = float(variant.get("keyword_inclusion", 0.5))
        platform_compliance = float(variant.get("platform_compliance", 1.0))

        score = (
            self.settings.engagement_predicted_weight * engagement_predicted
            + self.settings.tone_match_weight * tone_match
            + self.settings.cta_presence_weight * cta_present
            + self.settings.keyword_inclusion_weight * keyword_inclusion
            + self.settings.platform_compliance_weight * platform_compliance
        )

        variant["engagement_predicted"] = engagement_predicted
        variant["tone_match"] = tone_match
        variant["cta_present"] = bool(variant.get("cta_present", False))
        variant["keyword_inclusion"] = keyword_inclusion
        variant["platform_compliance"] = platform_compliance
        variant["final_score"] = max(0.0, min(1.0, score))
        return variant
