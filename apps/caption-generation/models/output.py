# FILE: apps/caption-generation/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import Platform, StrictBaseModel


class CaptionVariant(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    caption_text: str
    policy_compliance_score: float = Field(..., ge=0.0, le=1.0)
    engagement_predicted: float = Field(..., ge=0.0, le=1.0)
    tone_match: float = Field(..., ge=0.0, le=1.0)
    cta_present: bool
    keyword_inclusion: float = Field(..., ge=0.0, le=1.0)
    platform_compliance: float = Field(..., ge=0.0, le=1.0)
    final_score: float = Field(..., ge=0.0, le=1.0)


class CaptionGenerationOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    variants: list[CaptionVariant]
    selected_variants_by_platform: dict[str, CaptionVariant]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    degraded_mode: bool = False
    generated_at: datetime
