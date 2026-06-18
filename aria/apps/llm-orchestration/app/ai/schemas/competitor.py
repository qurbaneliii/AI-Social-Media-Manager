from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brand import BrandProfile


class CompetitorPostData(BaseModel):
    competitor_name: str
    platform: str
    content_type: str
    caption: str = ""
    hook: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    published_at: str | None = None
    engagement_metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompetitorAnalysisRequest(BaseModel):
    brand_profile: BrandProfile
    competitors: list[CompetitorPostData] = Field(default_factory=list)
    business_goal: str = ""
    platforms: list[str] = Field(default_factory=list)


class CompetitorInsightReport(BaseModel):
    top_performing_content_types: list[str] = Field(default_factory=list)
    hook_patterns: list[str] = Field(default_factory=list)
    recurring_themes: list[str] = Field(default_factory=list)
    hashtag_patterns: list[str] = Field(default_factory=list)
    tone_patterns: list[str] = Field(default_factory=list)
    posting_patterns: list[str] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    strategic_opportunities: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    source_limitations: list[str] = Field(default_factory=list)

