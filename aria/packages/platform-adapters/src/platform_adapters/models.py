from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class OAuthCredentials(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None


class PlatformConstraints(BaseModel):
    max_caption_chars: int
    max_hashtags: int
    supports_alt_text: bool
    supports_multi_media: bool


class CanonicalMedia(BaseModel):
    s3_key: str
    mime_type: str


class CanonicalContent(BaseModel):
    caption_text: str
    hashtags: list[str]
    media: list[CanonicalMedia]
    alt_text: str | None = None


class CanonicalPublishPayload(BaseModel):
    schedule_id: str
    company_id: str
    platform: str
    content: CanonicalContent
    credentials_ref: str | None = None
    idempotency_key: str = Field(min_length=8)


class PublishResult(BaseModel):
    status: str
    external_post_id: str | None = None
    error: dict[str, str] | None = None


class MetricRecord(BaseModel):
    company_id: str
    post_id: str
    platform: str
    external_post_id: str
    impressions: int
    reach: int
    engagement_rate: float
    click_through_rate: float
    saves: int
    shares: int
    follower_growth_delta: int
    posting_timestamp: datetime
    captured_at: datetime
    source: str


class WebhookEvent(BaseModel):
    event_type: str
    external_post_id: str
    occurred_at: datetime
    payload: dict
