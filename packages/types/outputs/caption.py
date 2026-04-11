# FILE: packages/types/outputs/caption.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import CTAType, Platform


class CaptionVariant(BaseModel):
    """Implements Section 3.2.1 Output A caption variant model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    platform: Platform
    caption_text: Annotated[str, Field(min_length=1, max_length=2200)]
    hashtags: Annotated[list[Annotated[str, Field(pattern=r"^#[a-z0-9_]{1,100}$")]], Field(max_length=30)] = Field(default_factory=list)
    cta_type: CTAType | None = None
    policy_compliance_score: float = Field(ge=0.0, le=1.0)
    engagement_predicted: float = Field(ge=0.0, le=1.0)
    tone_match: float = Field(ge=0.0, le=1.0)
    cta_present: bool
    keyword_inclusion: float = Field(ge=0.0, le=1.0)
    platform_compliance: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)


class CaptionGenerationOutput(BaseModel):
    """Implements Section 3.2.1 Output A caption generation response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    variants: Annotated[list[CaptionVariant], Field(min_length=1, max_length=60)]
    selected_variants_by_platform: dict[str, CaptionVariant]
    confidence_score: float = Field(ge=0.0, le=1.0)
    degraded_mode: bool = False
    generated_at: datetime

    @field_validator("variants")
    @classmethod
    def validate_unique_variant_platforms(cls, value: list[CaptionVariant]) -> list[CaptionVariant]:
        """Ensures variants contain unique platforms."""
        seen: set[str] = set()
        duplicates: set[str] = set()
        for item in value:
            key = str(item.platform)
            if key in seen:
                duplicates.add(key)
            seen.add(key)
        if duplicates:
            raise ValueError(f"Duplicate variant platforms found: {sorted(duplicates)}")
        return value

    @model_validator(mode="after")
    def validate_selected_variant_keys(self) -> "CaptionGenerationOutput":
        """Ensures selected variant keys align with variant platform values."""
        available_platforms = {str(item.platform) for item in self.variants}
        invalid = sorted(set(self.selected_variants_by_platform.keys()) - available_platforms)
        if invalid:
            raise ValueError(f"selected_variants_by_platform contains unknown platforms: {invalid}")
        return self
