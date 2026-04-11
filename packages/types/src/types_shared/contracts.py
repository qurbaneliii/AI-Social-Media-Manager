# FILE: packages/types/src/types_shared/contracts.py
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import StrictBaseModel
from .enums import Platform


class MetricRecord(StrictBaseModel):
    company_id: UUID
    post_id: UUID
    platform: Platform
    external_post_id: str = Field(..., min_length=1, max_length=255)
    impressions: int = Field(..., ge=0)
    reach: int = Field(..., ge=0)
    engagement_rate: float = Field(..., ge=0.0)
    click_through_rate: float = Field(..., ge=0.0)
    saves: int = Field(..., ge=0)
    shares: int = Field(..., ge=0)
    follower_growth_delta: int
    posting_timestamp: datetime
    captured_at: datetime
    source: str = Field(..., min_length=2, max_length=50)
    attributes: dict[str, Any] = Field(default_factory=dict)


class TimeWindow(StrictBaseModel):
    platform: Platform
    run_at_utc: datetime
    score: float = Field(..., ge=0.0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class HashtagCandidate(StrictBaseModel):
    hashtag: str = Field(..., pattern=r"^#?[a-zA-Z0-9_]{1,100}$")
    relevance_cosine: float = Field(..., ge=0.0, le=1.0)
    engagement_uplift: float = Field(..., ge=0.0)
    recency_trend: float = Field(..., ge=0.0)
    brand_fit: float = Field(..., ge=0.0, le=1.0)
    search_volume: int = Field(..., ge=0)
