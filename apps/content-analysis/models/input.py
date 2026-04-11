# FILE: apps/content-analysis/models/input.py
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from types_shared import StrictBaseModel


class SamplePost(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=2, max_length=5000, description="Historical post text")
    engagement_rate: float | None = Field(None, ge=0.0, le=1.0, description="Optional engagement rate")
    posted_at: datetime | None = Field(None, description="Original post timestamp")


class ContentAnalysisInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID = Field(..., description="Company identifier")
    target_locale: Literal["en", "auto"] = Field("auto", description="Target locale")
    descriptive_prior: dict[str, float] = Field(default_factory=dict, description="Prior tone dimensions")
    sample_posts: list[SamplePost] = Field(..., min_length=1, description="Historical posts sample")

    @field_validator("sample_posts")
    @classmethod
    def validate_non_empty_texts(cls, value: list[SamplePost]) -> list[SamplePost]:
        if not any(post.text.strip() for post in value):
            raise ValueError("At least one sample post must contain text")
        return value
