from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class Platform(str, Enum):
    instagram = "instagram"
    linkedin = "linkedin"
    facebook = "facebook"
    x = "x"
    tiktok = "tiktok"
    pinterest = "pinterest"


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: UUID
    retryable: bool


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class TargetMarket(BaseModel):
    regions: list[str]
    segments: list[Literal["B2B", "B2C", "D2C"]]
    persona_summary: str


class PlatformPresence(BaseModel):
    instagram: bool
    linkedin: bool
    facebook: bool
    x: bool
    tiktok: bool
    pinterest: bool


class PostingFrequencyGoal(BaseModel):
    instagram: int
    linkedin: int
    facebook: int
    x: int
    tiktok: int
    pinterest: int


class PreviousPostArchive(BaseModel):
    format: Literal["csv", "json"]
    s3_uri: str | None = None


class CompanyProfileRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    industry_vertical: str
    target_market: TargetMarket
    brand_positioning_statement: str = Field(min_length=30, max_length=500)
    tone_of_voice_descriptors: list[str]
    competitor_list: list[str]
    platform_presence: PlatformPresence
    posting_frequency_goal: PostingFrequencyGoal
    primary_cta_types: list[str]
    brand_color_hex_codes: list[str]
    approved_vocabulary_list: list[str]
    banned_vocabulary_list: list[str]
    previous_post_archive: PreviousPostArchive | None = None
    brand_guidelines_pdf: str | None = None
    logo_file: UUID | None = None
    sample_post_images: list[UUID | None]

    @field_validator("brand_color_hex_codes")
    @classmethod
    def validate_hex_codes(cls, values: list[str]) -> list[str]:
        for value in values:
            if len(value) != 7 or not value.startswith("#"):
                raise ValueError("Hex colors must be in #RRGGBB format")
        return values


class CompanyProfileResponse(BaseModel):
    company_id: UUID
    profile_version: int
    status: Literal["submitted"]


class MediaPresignRequest(BaseModel):
    company_id: UUID
    file_name: str
    mime_type: str
    size_bytes: int = Field(gt=0)


class MediaPresignResponse(BaseModel):
    media_id: UUID
    upload_url: str
    s3_key: str


class PostGenerateRequest(BaseModel):
    company_id: UUID
    post_intent: Literal["announce", "educate", "promote", "engage", "inspire", "crisis_response"]
    core_message: str = Field(min_length=20, max_length=500)
    target_platforms: list[Platform]
    campaign_tag: str | None = None
    attached_media_id: UUID | None = None
    manual_keywords: list[str]
    urgency_level: Literal["scheduled", "immediate"]
    requested_publish_at: datetime | None = None


class PostGenerateResponse(BaseModel):
    post_id: UUID
    status: Literal["generating", "generated"]
    estimated_ready_seconds: int


class ScheduleTarget(BaseModel):
    platform: Platform
    run_at_utc: datetime


class ManualOverride(BaseModel):
    timezone: str
    force_window: bool


class ScheduleRequest(BaseModel):
    post_id: UUID
    company_id: UUID
    targets: list[ScheduleTarget]
    approval_mode: Literal["human", "auto"]
    manual_override: ManualOverride


class ScheduleResponse(BaseModel):
    schedule_ids: list[UUID]
    status: Literal["queued"]


class CanonicalContent(BaseModel):
    caption_text: str
    hashtags: list[str]
    media: list[dict[str, str]]
    alt_text: str | None = None


class TrackingUTM(BaseModel):
    source: str
    medium: str
    campaign: str


class Tracking(BaseModel):
    campaign_tag: str
    utm: TrackingUTM


class CanonicalPublishPayload(BaseModel):
    schedule_id: UUID
    company_id: UUID
    platform: Platform
    content: CanonicalContent
    credentials_ref: UUID | None = None
    idempotency_key: str | None = None
    tracking: Tracking | None = None


class PublishError(BaseModel):
    code: str
    message: str


class PublishResponse(BaseModel):
    status: Literal["published", "failed"]
    external_post_id: str | None = None
    error: PublishError | None = None


class AnalyticsRecord(BaseModel):
    post_id: UUID
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


class AnalyticsIngestRequest(BaseModel):
    records: list[AnalyticsRecord]


class AnalyticsIngestError(BaseModel):
    index: int
    reason: str


class AnalyticsIngestResponse(BaseModel):
    ingested_count: int
    rejected_count: int
    errors: list[AnalyticsIngestError]


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMProxyRequest(BaseModel):
    provider: Literal["deepseek", "openai", "anthropic", "mistral"]
    model: str
    messages: list[LLMMessage]
    response_format: Literal["json", "text"]
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int
    cache_key: str | None = None


class TokenUsage(BaseModel):
    input: int
    output: int


class LLMProxyResponse(BaseModel):
    provider_used: str
    model_used: str
    output: str | dict[str, Any]
    token_usage: TokenUsage
    cached: bool


class ModuleResultEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: Literal["module.result.ready.v1"]
    tenant_id: UUID
    company_id: UUID
    schema_version: Literal[1] = 1
    emitted_at: datetime
    payload: dict[str, Any]
