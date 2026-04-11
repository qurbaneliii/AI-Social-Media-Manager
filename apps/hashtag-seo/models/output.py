# FILE: apps/hashtag-seo/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import StrictBaseModel


class RankedHashtag(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    hashtag: str = Field(..., pattern=r"^#[a-z0-9_]{1,100}$")
    score: float = Field(..., ge=0.0)
    tier: str = Field(..., pattern=r"^(broad|niche|micro)$")


class SeoMetadata(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    meta_title: str = Field(..., max_length=60)
    meta_description: str = Field(..., max_length=160)
    alt_text: str = Field(..., max_length=220)


class HashtagSeoOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    hashtags: list[RankedHashtag]
    seo_metadata: SeoMetadata
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    degraded_mode: bool = False
    generated_at: datetime
