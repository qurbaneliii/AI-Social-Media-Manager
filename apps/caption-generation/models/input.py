# FILE: apps/caption-generation/models/input.py
from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import Platform, PostIntent, StrictBaseModel


class CaptionGenerationInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    post_intent: PostIntent
    core_message: str = Field(..., min_length=20, max_length=500)
    target_platforms: list[Platform] = Field(..., min_length=1)
    banned_vocabulary_list: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    tone_fingerprint: dict = Field(default_factory=dict)
    visual_profile: dict = Field(default_factory=dict)
    hashtags: list[str] = Field(default_factory=list)
    audience_profile: dict = Field(default_factory=dict)
    ranked_windows: list[dict] = Field(default_factory=list)
