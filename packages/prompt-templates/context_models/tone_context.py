# FILE: packages/prompt-templates/context_models/tone_context.py
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from packages.types.enums import Platform


class SamplePost(BaseModel):
    text: str = Field(min_length=20)
    platform: Platform
    engagement_rate: float | None = Field(default=None, ge=0.0, le=1.0)


class ToneContext(BaseModel):
    company_id: UUID
    company_name: str = Field(min_length=2)
    tone_descriptors: list[str] = Field(min_length=3, max_length=20)
    brand_positioning: str = Field(min_length=30)
    sample_posts: list[SamplePost] = Field(min_length=5)
    competitor_tone_analysis: str = ""
    approved_vocabulary: list[str] = Field(default_factory=list)
    banned_vocabulary: list[str] = Field(default_factory=list)
