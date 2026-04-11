# FILE: apps/hashtag-seo/services/scoring_engine.py
from __future__ import annotations

import math

from config import Settings


class ScoringEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def process(self, tokens: list[str], vector_candidates: list[dict]) -> list[dict]:
        """Apply required weighted score formula over relevance, uplift, recency, and brand fit."""
        by_token = {str(c.get("hashtag", "")).lower().lstrip("#"): c for c in vector_candidates}
        scored: list[dict] = []

        for idx, token in enumerate(tokens):
            source = by_token.get(token, {})
            relevance = float(source.get("relevance", max(0.0, 1 - idx / max(len(tokens), 1))))
            uplift = float(source.get("performance_weight", 0.1))
            recency = max(0.0, 1.0 - (idx / max(len(tokens), 1)))
            brand_fit = min(1.0, 0.4 + (len(token) / 30.0))
            score = (
                self.settings.relevance_cosine_weight * relevance
                + self.settings.engagement_uplift_weight * uplift
                + self.settings.recency_trend_weight * recency
                + self.settings.brand_fit_weight * brand_fit
            )
            volume = int(source.get("metadata_json", {}).get("search_volume", max(1000, int(math.exp(min(len(token), 10)) * 1000))))
            scored.append({"token": token, "score": score, "search_volume": volume})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored
