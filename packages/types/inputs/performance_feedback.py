# FILE: packages/types/inputs/performance_feedback.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import Platform


class PerformanceFeedback(BaseModel):
    """Implements Section 3.1.3 Input C single performance feedback record."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    post_id: UUID
    platform: Platform
    external_post_id: Annotated[str, Field(min_length=1, max_length=255)]
    impressions: int = Field(ge=0)
    reach: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0, le=1.0)
    click_through_rate: float = Field(ge=0.0, le=1.0)
    saves: int = Field(ge=0)
    shares: int = Field(ge=0)
    follower_growth_delta: int
    posting_timestamp: datetime
    captured_at: datetime

    @model_validator(mode="after")
    def validate_feedback_consistency(self) -> "PerformanceFeedback":
        """Checks reach/impressions and captured/posting timestamp consistency rules."""
        if self.reach > self.impressions:
            raise ValueError("reach must be <= impressions")
        if self.captured_at < self.posting_timestamp:
            raise ValueError("captured_at must be >= posting_timestamp")
        return self


class PerformanceFeedbackBatch(BaseModel):
    """Implements Section 3.1.3 Input C batched performance feedback payload."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    records: Annotated[list[PerformanceFeedback], Field(min_length=1, max_length=500)]

    @field_validator("records")
    @classmethod
    def validate_unique_post_platform_pairs(cls, value: list[PerformanceFeedback]) -> list[PerformanceFeedback]:
        """Ensures no duplicate (post_id, platform) combinations within a batch."""
        seen: set[tuple[str, str]] = set()
        duplicates: set[tuple[str, str]] = set()
        for record in value:
            key = (str(record.post_id), str(record.platform))
            if key in seen:
                duplicates.add(key)
            seen.add(key)
        if duplicates:
            formatted = [f"{post_id}:{platform}" for post_id, platform in sorted(duplicates)]
            raise ValueError(f"Duplicate (post_id, platform) records found: {formatted}")
        return value
