# FILE: packages/types/outputs/audience.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..enums import Platform


class AgeRange(BaseModel):
    """Implements Section 3.2.3 Output C age range model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    min_age: int = Field(ge=13, le=80)
    max_age: int = Field(ge=13, le=90)

    @model_validator(mode="after")
    def validate_age_bounds(self) -> "AgeRange":
        """Ensures min_age is not greater than max_age."""
        if self.min_age > self.max_age:
            raise ValueError("min_age must be <= max_age")
        return self


class AudienceProfile(BaseModel):
    """Implements Section 3.2.3 Output C audience profile model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    age_range: AgeRange
    segments: Annotated[list[Annotated[str, Field(min_length=1, max_length=80)]], Field(min_length=1, max_length=20)]
    psychographics: dict[str, float] = Field(default_factory=dict)
    platform_segments: dict[Platform, list[Annotated[str, Field(min_length=1, max_length=80)]]] = Field(default_factory=dict)


class AudienceOutput(BaseModel):
    """Implements Section 3.2.3 Output C audience targeting response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    profile: AudienceProfile
    warning_codes: list[Annotated[str, Field(min_length=1, max_length=64)]] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    requires_approval: bool = False
    generated_at: datetime
