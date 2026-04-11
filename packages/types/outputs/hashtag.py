# FILE: packages/types/outputs/hashtag.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RankedHashtag(BaseModel):
    """Implements Section 3.2.2 Output B ranked hashtag candidate."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    hashtag: Annotated[str, Field(pattern=r"^#[a-z0-9_]{1,100}$")]
    score: float = Field(ge=0.0)
    tier: Annotated[str, Field(pattern=r"^(broad|niche|micro)$")]


class HashtagOutput(BaseModel):
    """Implements Section 3.2.2 Output B hashtag response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    hashtags: Annotated[list[RankedHashtag], Field(min_length=1, max_length=100)]
    confidence_score: float = Field(ge=0.0, le=1.0)
    degraded_mode: bool = False
    generated_at: datetime

    @field_validator("hashtags")
    @classmethod
    def validate_unique_hashtags(cls, value: list[RankedHashtag]) -> list[RankedHashtag]:
        """Ensures hashtag list is unique by normalized hashtag value."""
        normalized = [item.hashtag.casefold() for item in value]
        duplicates = sorted({item for item in normalized if normalized.count(item) > 1})
        if duplicates:
            raise ValueError(f"Duplicate hashtags are not allowed: {duplicates}")
        return value
