from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .brand import BrandProfile
from .evaluation import AIQualityReview


class PlatformContext(BaseModel):
    platform: str
    content_type: str
    audience_segment: str = ""
    objective: str
    tone_override: str | None = None
    character_limit: int | None = Field(default=None, gt=0)
    hashtag_limit: int | None = Field(default=None, ge=0)
    format_rules: list[str] = Field(default_factory=list)


class ContentRequest(BaseModel):
    brand_profile: BrandProfile
    platform_context: PlatformContext
    campaign_objective: str
    topic: str
    content_pillar: str
    language: str = "en"
    number_of_variants: int = Field(default=1, ge=1, le=5)
    extra_context: dict[str, Any] = Field(default_factory=dict)


class GeneratedContentPackage(BaseModel):
    platform: str
    content_type: str
    hook: str
    caption: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    visual_brief: dict[str, Any] = Field(default_factory=dict)
    video_script: str | None = None
    carousel_structure: list[dict[str, Any]] = Field(default_factory=list)
    posting_recommendation: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    risks: list[str] = Field(default_factory=list)
    quality_scores: AIQualityReview | None = None

    @field_validator("hashtags")
    @classmethod
    def hashtags_start_with_hash(cls, values: list[str]) -> list[str]:
        return [tag if tag.startswith("#") else f"#{tag}" for tag in values]

