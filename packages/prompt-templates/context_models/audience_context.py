# FILE: packages/prompt-templates/context_models/audience_context.py
from __future__ import annotations

import json
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from packages.types.enums import MarketSegment, Platform, PostIntent


class PerformanceSegment(BaseModel):
    segment: str
    engagement_lift: float = Field(ge=-1.0, le=10.0)


class AudienceContext(BaseModel):
    company_id: UUID
    platforms: list[Platform] = Field(min_length=1)
    company_profile_json: str
    post_intent: PostIntent
    content_topic: str = Field(min_length=5)
    value_prop: str = Field(min_length=10)
    top_segments: list[PerformanceSegment] = Field(default_factory=list)
    weak_segments: list[str] = Field(default_factory=list)
    historical_notes: str = ""
    market_segment: MarketSegment = MarketSegment.B2C

    @field_validator("company_profile_json")
    @classmethod
    def validate_company_profile_json(cls, value: str) -> str:
        try:
            json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("company_profile_json must be valid JSON") from exc
        return value
