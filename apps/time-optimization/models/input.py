# FILE: apps/time-optimization/models/input.py
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from types_shared import Platform, StrictBaseModel


class HistoricalPost(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    day_of_week: int = Field(..., ge=0, le=6)
    hour_of_day: int = Field(..., ge=0, le=23)
    content_type: str = Field(..., min_length=2, max_length=50)
    recency_decay: float = Field(..., ge=0.0, le=1.0)
    engagement_rate: float = Field(..., ge=0.0)


class EventImpact(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    impact: float = Field(..., ge=0.0, le=1.0)


class TimeOptimizationInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    industry: str = Field(..., min_length=2, max_length=80)
    target_platforms: list[Platform] = Field(..., min_length=1)
    historical_posts: list[HistoricalPost] = Field(default_factory=list)
    event_calendar: list[EventImpact] = Field(default_factory=list)
    competitor_activity_density: dict[str, float] = Field(default_factory=dict)
    posting_frequency_goal: dict[str, int] = Field(default_factory=dict)

    @field_validator("posting_frequency_goal")
    @classmethod
    def validate_goal(cls, value: dict[str, int]) -> dict[str, int]:
        if any(v <= 0 for v in value.values()):
            raise ValueError("posting_frequency_goal values must be positive")
        return value
