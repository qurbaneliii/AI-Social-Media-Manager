# FILE: packages/prompt-templates/context_models/seo_context.py
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from packages.types.enums import MarketSegment, Platform


class SEOContext(BaseModel):
    company_id: UUID
    post_caption: str = Field(min_length=10)
    image_description: str = ""
    industry_vertical: str = Field(min_length=2)
    target_keywords: list[str] = Field(min_length=1, max_length=5)
    secondary_keywords: list[str] = Field(default_factory=list, max_length=10)
    platform: Platform
    market_segment: MarketSegment = MarketSegment.B2C
    banned_vocabulary: list[str] = Field(default_factory=list)
