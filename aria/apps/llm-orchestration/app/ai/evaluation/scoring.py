from __future__ import annotations

from ai.schemas.evaluation import AIQualityReview


def aggregate_quality_score(review: AIQualityReview) -> float:
    positive = [
        review.brand_consistency_score,
        review.platform_fit_score,
        review.clarity_score,
        review.cta_strength_score,
        review.originality_score,
        review.engagement_potential_score,
    ]
    risk_penalty = (review.factual_risk_score + review.safety_risk_score) / 2
    return round(max(0.0, min(1.0, (sum(positive) / len(positive)) - (risk_penalty * 0.25))), 4)

