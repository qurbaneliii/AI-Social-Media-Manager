# FILE: packages/prompt-templates/context_models/caption_context.py
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from packages.types.enums import Platform, PostIntent


class PlatformConstraints(BaseModel):
    platform: Platform
    max_chars: int
    supports_hashtags: bool
    supports_links: bool
    supports_emojis: bool


class CaptionContext(BaseModel):
    company_id: UUID
    company_name: str = Field(min_length=2, max_length=120)
    company_positioning: str = Field(min_length=10)
    tone_fingerprint: dict[str, Any]
    approved_vocabulary_list: list[str] = Field(default_factory=list)
    banned_vocabulary_list: list[str] = Field(default_factory=list)
    post_intent: PostIntent
    core_message: str = Field(min_length=20, max_length=500)
    campaign_tag: str | None = None
    cta_requirements: list[str] = Field(min_length=1)
    visual_context_summary: str = ""
    image_ocr_text: str = ""
    visual_tone_scores: dict[str, float] = Field(default_factory=dict)
    audience_profile: dict[str, Any]
    seo_keywords: list[str] = Field(min_length=1)
    secondary_keywords: list[str] = Field(default_factory=list)
    target_platforms: list[Platform] = Field(min_length=1)
    platform_constraints: list[PlatformConstraints] = Field(min_length=1)

    @field_validator("tone_fingerprint")
    @classmethod
    def validate_tone_fingerprint_non_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("tone_fingerprint must be a non-empty dict")
        return value

    @field_validator("audience_profile")
    @classmethod
    def validate_audience_profile_non_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("audience_profile must be a non-empty dict")
        return value

    @model_validator(mode="after")
    def validate_platform_constraints_coverage(self) -> "CaptionContext":
        constrained = {item.platform.value for item in self.platform_constraints}
        missing = [platform.value for platform in self.target_platforms if platform.value not in constrained]
        if missing:
            raise ValueError(f"Missing platform_constraints for target platforms: {missing}")
        return self
