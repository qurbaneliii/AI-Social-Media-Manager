from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brand import BrandProfile


class TrendInputData(BaseModel):
    keyword: str
    source: str = "provided"
    platform: str | None = None
    signals: dict[str, Any] = Field(default_factory=dict)
    examples: list[str] = Field(default_factory=list)


class TrendResearchRequest(BaseModel):
    brand_profile: BrandProfile
    trends: list[TrendInputData] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    business_goal: str = ""


class TrendInsightReport(BaseModel):
    relevant_topics: list[str] = Field(default_factory=list)
    recommended_hashtags: list[str] = Field(default_factory=list)
    content_formats: list[str] = Field(default_factory=list)
    trend_opportunities: list[str] = Field(default_factory=list)
    platform_notes: dict[str, list[str]] = Field(default_factory=dict)
    risk_notes: list[str] = Field(default_factory=list)
    source_limitations: list[str] = Field(default_factory=list)

