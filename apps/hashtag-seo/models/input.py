# FILE: apps/hashtag-seo/models/input.py
from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import Platform, StrictBaseModel


class HashtagSeoInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    target_platform: Platform
    core_text: str = Field(..., min_length=20, max_length=5000)
    keywords: list[str] = Field(..., min_length=1, max_length=40)
    banned_tags: list[str] = Field(default_factory=list)
