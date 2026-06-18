from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .brand import BrandProfile
from .content import PlatformContext


class HashtagRecommendationRequest(BaseModel):
    brand_profile: BrandProfile
    platform_context: PlatformContext
    topic: str
    campaign_name: str | None = None
    location: str | None = None
    trend_keywords: list[str] = Field(default_factory=list)
    max_hashtags: int = Field(default=12, ge=1, le=30)


class HashtagRecommendation(BaseModel):
    niche_hashtags: list[str] = Field(default_factory=list)
    broad_hashtags: list[str] = Field(default_factory=list)
    branded_hashtags: list[str] = Field(default_factory=list)
    campaign_hashtags: list[str] = Field(default_factory=list)
    location_hashtags: list[str] = Field(default_factory=list)
    trend_based_hashtags: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    rationale: str

    @field_validator(
        "niche_hashtags",
        "broad_hashtags",
        "branded_hashtags",
        "campaign_hashtags",
        "location_hashtags",
        "trend_based_hashtags",
    )
    @classmethod
    def hashtags_start_with_hash(cls, values: list[str]) -> list[str]:
        return [tag if tag.startswith("#") else f"#{tag}" for tag in values]

