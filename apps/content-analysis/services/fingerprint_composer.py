# FILE: apps/content-analysis/services/fingerprint_composer.py
from __future__ import annotations

import numpy as np


class FingerprintComposer:
    def __init__(
        self,
        descriptive_prior_weight: float,
        corpus_stats_weight: float,
        engagement_delta_weight: float,
        sparse_sample_confidence_cap: float,
    ) -> None:
        self.descriptive_prior_weight = descriptive_prior_weight
        self.corpus_stats_weight = corpus_stats_weight
        self.engagement_delta_weight = engagement_delta_weight
        self.sparse_sample_confidence_cap = sparse_sample_confidence_cap

    async def process(
        self,
        descriptive_prior: dict[str, float],
        sentiment_scores: list[float],
        correlation: float,
        sample_count: int,
    ) -> tuple[dict[str, float], float, bool]:
        """Blend prior, corpus stats, and engagement deltas using the required weighted formula."""
        prior_tone = float(descriptive_prior.get("tone", 0.5))
        prior_energy = float(descriptive_prior.get("energy", 0.5))

        sentiment_mean = float(np.mean(sentiment_scores)) if sentiment_scores else 0.0
        corpus_component = 0.5 + (sentiment_mean / 2)
        engagement_component = 0.5 + (correlation / 2)

        degraded_mode = False
        if sample_count < 10:
            degraded_mode = True
            fingerprint = {
                "tone": round(prior_tone, 6),
                "energy": round(prior_energy, 6),
                "confidence": self.sparse_sample_confidence_cap,
            }
            return fingerprint, self.sparse_sample_confidence_cap, degraded_mode

        blend = (
            self.descriptive_prior_weight * prior_tone
            + self.corpus_stats_weight * corpus_component
            + self.engagement_delta_weight * engagement_component
        )
        confidence = max(0.0, min(1.0, blend))

        fingerprint = {
            "tone": round(blend, 6),
            "energy": round((prior_energy * 0.5 + corpus_component * 0.5), 6),
            "confidence": round(confidence, 6),
        }
        return fingerprint, confidence, degraded_mode
