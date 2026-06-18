from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ApprovalStatus = Literal["approved", "needs_revision", "requires_human_review"]


class AIQualityReview(BaseModel):
    brand_consistency_score: float = Field(ge=0.0, le=1.0)
    platform_fit_score: float = Field(ge=0.0, le=1.0)
    clarity_score: float = Field(ge=0.0, le=1.0)
    cta_strength_score: float = Field(ge=0.0, le=1.0)
    originality_score: float = Field(ge=0.0, le=1.0)
    factual_risk_score: float = Field(ge=0.0, le=1.0)
    safety_risk_score: float = Field(ge=0.0, le=1.0)
    engagement_potential_score: float = Field(ge=0.0, le=1.0)
    approval_status: ApprovalStatus
    improvement_notes: list[str] = Field(default_factory=list)

