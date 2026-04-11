# FILE: packages/types/enums.py
from __future__ import annotations

from enum import StrEnum


class Platform(StrEnum):
    """Implements Section 3 shared platform enumeration."""

    instagram = "instagram"
    linkedin = "linkedin"
    facebook = "facebook"
    x = "x"
    tiktok = "tiktok"
    pinterest = "pinterest"


class PostIntent(StrEnum):
    """Implements Section 3 post intent enumeration."""

    announce = "announce"
    educate = "educate"
    promote = "promote"
    engage = "engage"
    inspire = "inspire"
    crisis_response = "crisis_response"


class UrgencyLevel(StrEnum):
    """Implements Section 3 urgency level enumeration."""

    scheduled = "scheduled"
    immediate = "immediate"


class CTAType(StrEnum):
    """Implements Section 3 CTA type enumeration."""

    learn_more = "learn_more"
    book_demo = "book_demo"
    buy_now = "buy_now"
    download = "download"
    comment = "comment"
    share = "share"


class MarketSegment(StrEnum):
    """Implements Section 3 market segment enumeration."""

    B2B = "B2B"
    B2C = "B2C"
    D2C = "D2C"


class PostArchiveFormat(StrEnum):
    """Implements Section 3 post archive format enumeration."""

    csv = "csv"
    json = "json"


class ScheduleStatus(StrEnum):
    """Implements Section 3 schedule status enumeration."""

    queued = "queued"
    awaiting_approval = "awaiting_approval"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    dead_letter = "dead_letter"
    expired = "expired"


class ApprovalMode(StrEnum):
    """Implements Section 3 approval mode enumeration."""

    human = "human"
    auto = "auto"


class LayoutType(StrEnum):
    """Implements Section 3 layout type enumeration."""

    minimalist = "minimalist"
    grid = "grid"
    text_overlay = "text_overlay"
    photographic = "photographic"
    illustrative = "illustrative"
    mixed = "mixed"
    unknown = "unknown"


class FontStyle(StrEnum):
    """Implements Section 3 font style enumeration."""

    sans = "sans"
    serif = "serif"
    display = "display"
    handwritten = "handwritten"
    mixed = "mixed"


class ReadingLevel(StrEnum):
    """Implements Section 3 reading level enumeration."""

    grade_6_to_8 = "grade_6_to_8"
    grade_9_to_12 = "grade_9_to_12"
    professional = "professional"


class RiskFlag(StrEnum):
    """Implements Section 3 risk flag enumeration."""

    over_promotional = "over_promotional"
    jargon_heavy = "jargon_heavy"
    inconsistent_tone = "inconsistent_tone"


class ReasonCode(StrEnum):
    """Implements Section 3 scheduling reason code enumeration."""

    historical_win = "historical_win"
    industry_baseline = "industry_baseline"
    low_competitor_density = "low_competitor_density"
    cold_start = "cold_start"
    event_boost = "event_boost"
    competitor_penalty = "competitor_penalty"
