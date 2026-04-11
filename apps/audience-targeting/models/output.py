# FILE: apps/audience-targeting/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import StrictBaseModel


class AgeRange(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    min_age: int = Field(..., ge=13, le=80)
    max_age: int = Field(..., ge=13, le=90)


class AudienceProfile(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    age_range: AgeRange
    segments: list[str]
    psychographics: dict[str, float]
    platform_segments: dict[str, list[str]]


class AudienceTargetingOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    profile: AudienceProfile
    warning_codes: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_approval: bool = False
    generated_at: datetime
