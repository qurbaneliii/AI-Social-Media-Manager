# FILE: packages/decision-engine/models.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


# -- Shared ----------------------------------------------------------------
class Platform(StrEnum):
    instagram = "instagram"
    linkedin = "linkedin"
    facebook = "facebook"
    x = "x"
    tiktok = "tiktok"
    pinterest = "pinterest"


class PostIntent(StrEnum):
    announce = "announce"
    educate = "educate"
    promote = "promote"
    engage = "engage"
    inspire = "inspire"
    crisis_response = "crisis_response"


# -- 5.1 Hashtag Selection Models ------------------------------------------
class HashtagCandidate(FrozenModel):
    tag: str
    embedding: list[float]
    monthly_volume: int = Field(ge=0)
    days_since_peak: int = Field(ge=0)
    historical_engagement_uplift: float = Field(ge=-1.0, le=10.0)
    brand_alignment_score: float = Field(ge=0.0, le=1.0)
    source: Literal["llm", "vector"]


class HashtagEntry(FrozenModel):
    tag: str
    score: float
    tier: Literal["broad", "niche", "micro"]
    source: Literal["llm", "vector", "borrowed"]


class HashtagSet(FrozenModel):
    broad: list[HashtagEntry]
    niche: list[HashtagEntry]
    micro: list[HashtagEntry]
    platform_cap_enforced: bool
    underfilled_tiers: list[str]


class HashtagSelectionInput(FrozenModel):
    candidates_llm: list[HashtagCandidate]
    candidates_vector: list[HashtagCandidate]
    topic_embedding: list[float]
    banned_tags: list[str]
    platform: Platform
    company_profile_embedding: list[float]


# -- 5.2 Audience Resolution Models ----------------------------------------
class AgeRange(FrozenModel):
    lower: int = Field(ge=13, le=98)
    upper: int = Field(ge=14, le=99)

    @model_validator(mode="after")
    def validate_bounds(self) -> "AgeRange":
        if self.lower >= self.upper:
            raise ValueError("lower must be < upper")
        return self


class LocationSet(FrozenModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class AudienceConfig(FrozenModel):
    """Company-configured mandatory audience constraints."""

    age_range: AgeRange
    locations: list[str]
    interests: list[str]
    mandatory_inclusions: list[str] = Field(default_factory=list)
    mandatory_exclusions: list[str] = Field(default_factory=list)
    compliance_restrictions: list[str] = Field(default_factory=list)


class AudienceProfile(FrozenModel):
    """Fully resolved audience after merge."""

    age_range: AgeRange
    locations: LocationSet
    interests: list[str]
    values: list[str]
    pain_points: list[str]
    psychographics: dict[str, list[str]]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_approval: bool = False
    override_codes: list[str] = Field(default_factory=list)
    llm_contribution_weight: float = Field(ge=0.0, le=1.0)


class AudienceResolutionInput(FrozenModel):
    company_config: AudienceConfig
    llm_inferred: AudienceProfile
    historical_top_segments: list[dict] = Field(default_factory=list)
    post_intent: PostIntent


# -- 5.3 Posting Time Models -----------------------------------------------
class TimeWindow(FrozenModel):
    start_utc: datetime
    end_utc: datetime
    rank: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    queue_utilization: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_window(self) -> "TimeWindow":
        if self.end_utc <= self.start_utc:
            raise ValueError("end_utc must be > start_utc")
        return self


class ManualOverride(FrozenModel):
    requested_utc: datetime
    timezone: str


class ScheduleContext(FrozenModel):
    platform: Platform
    ranked_windows: list[TimeWindow] = Field(min_length=1)
    last_posted_utc: datetime | None = None
    campaign_deadline_utc: datetime | None = None
    manual_override: ManualOverride | None = None
    audience_region_weights: dict[str, float] = Field(default_factory=dict)
    current_utc: datetime


class PostingTimeResult(FrozenModel):
    selected_window: TimeWindow
    was_override_used: bool
    was_fallback_used: bool
    override_rejection_reason: str | None = None
    cooldown_enforced: bool


# -- 5.4 Tone Adaptation Models --------------------------------------------
class ToneFingerprint(FrozenModel):
    formality_score: int = Field(ge=0, le=100)
    humor_score: int = Field(ge=0, le=100)
    assertiveness_score: int = Field(ge=0, le=100)
    optimism_score: int = Field(ge=0, le=100)
    emoji_density_target: float = Field(ge=0.0, le=1.0)
    avg_sentence_length_target: float
    clarity_score: int = Field(default=50, ge=0, le=100)
    urgency_score: int = Field(default=50, ge=0, le=100)
    warmth_score: int = Field(default=50, ge=0, le=100)
    empathy_score: int = Field(default=50, ge=0, le=100)
    storytelling_score: int = Field(default=50, ge=0, le=100)
    preferred_cta_types: list[str]
    style_rules: list[str]
    forbidden_terms: list[str]


class ToneAdaptationInput(FrozenModel):
    base_fingerprint: ToneFingerprint
    post_intent: PostIntent
    platform: Platform


class ToneAdaptationResult(FrozenModel):
    adapted_fingerprint: ToneFingerprint
    applied_intent_deltas: dict[str, int]
    applied_platform_modifiers: dict[str, int | float]
    crisis_mode_active: bool
    clamped_dimensions: list[str]


# -- 5.5 Platform Routing Models -------------------------------------------
class MediaAsset(FrozenModel):
    media_id: str
    width_px: int = Field(ge=1)
    height_px: int = Field(ge=1)
    mime_type: str


class PlatformCaptionState(FrozenModel):
    platform: Platform
    current_char_count: int
    char_limit: int
    overflow_ratio: float


class PlatformRoutingInput(FrozenModel):
    target_platforms: list[Platform] = Field(min_length=1)
    style_distance: float = Field(ge=0.0, le=1.0)
    media_asset: MediaAsset | None = None
    caption_states: list[PlatformCaptionState] = Field(default_factory=list)
    hashtag_set: dict


class PlatformRoutingDecision(FrozenModel):
    platform: Platform
    caption_strategy: Literal["shared_base", "per_platform"]
    hashtag_selection: list[str]
    requires_media_transform: bool
    media_transform_reason: str | None = None
    caption_action: Literal["use_as_is", "semantic_truncate", "regenerate"]
    caption_action_reason: str | None = None


class PlatformRoutingPlan(FrozenModel):
    decisions: list[PlatformRoutingDecision]
    global_strategy: Literal["shared_base", "per_platform"]
