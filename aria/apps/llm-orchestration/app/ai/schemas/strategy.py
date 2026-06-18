from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brand import BrandProfile


class BrandStrategyRequest(BaseModel):
    brand_profile: BrandProfile
    business_goal: str
    platforms: list[str] = Field(default_factory=list)
    market_context: dict[str, Any] = Field(default_factory=dict)


class BrandStrategyPlan(BaseModel):
    positioning_statement: str
    audience_hypotheses: list[str] = Field(default_factory=list)
    content_pillars: list[str] = Field(default_factory=list)
    campaign_angles: list[str] = Field(default_factory=list)
    platform_recommendations: dict[str, list[str]] = Field(default_factory=dict)
    strategic_recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    approval_required: bool = True

