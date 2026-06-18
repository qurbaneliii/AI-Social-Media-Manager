from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BrandProfile(BaseModel):
    brand_id: str
    brand_name: str
    industry: str
    description: str = ""
    products_or_services: list[str] = Field(default_factory=list)
    target_audience: list[str] = Field(default_factory=list)
    tone_of_voice: list[str] = Field(default_factory=list)
    brand_values: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    forbidden_words: list[str] = Field(default_factory=list)
    approved_claims: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    visual_style: dict[str, Any] = Field(default_factory=dict)
    business_goals: list[str] = Field(default_factory=list)
    language_preferences: list[str] = Field(default_factory=lambda: ["en"])

