from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HashtagCandidate:
    tag: str
    relevance: float
    historical_score: float


@dataclass(frozen=True)
class PlatformConstraints:
    max_hashtags: int
    allow_duplicates: bool


@dataclass(frozen=True)
class HashtagSet:
    selected: list[str]


@dataclass(frozen=True)
class AudienceConfig:
    locked_segments: list[str]
    locked: bool


@dataclass(frozen=True)
class AudienceProfile:
    segments: list[str]
    confidence: float


@dataclass(frozen=True)
class TimeWindow:
    run_at_utc: str
    confidence: float


@dataclass(frozen=True)
class ScheduleContext:
    force_window: bool
    minimum_confidence: float


@dataclass(frozen=True)
class ToneFingerprint:
    warmth: float
    authority: float
    playfulness: float


PostIntent = Literal["announce", "educate", "promote", "engage", "inspire", "crisis_response"]


@dataclass(frozen=True)
class PostRequest:
    target_platforms: list[str]
    urgency_level: str


@dataclass(frozen=True)
class BrandProfile:
    platform_enabled: bool


@dataclass(frozen=True)
class PlatformRoutingPlan:
    selected_platforms: list[str]


def select_hashtags(candidates: list[HashtagCandidate], platform: str, constraints: PlatformConstraints) -> HashtagSet:
    """Select hashtags by deterministic weighted rank and platform cap.

    Rule: score = 0.7 * relevance + 0.3 * historical_score.
    If duplicates are disallowed, deduplicate by tag while preserving rank order.
    Return top-N where N equals platform max hashtag constraint.
    """
    scored = sorted(candidates, key=lambda c: (0.7 * c.relevance + 0.3 * c.historical_score), reverse=True)
    chosen: list[str] = []
    seen: set[str] = set()
    for c in scored:
        if not constraints.allow_duplicates and c.tag in seen:
            continue
        seen.add(c.tag)
        chosen.append(c.tag)
        if len(chosen) >= constraints.max_hashtags:
            break
    return HashtagSet(selected=chosen)


def resolve_audience(company_config: AudienceConfig, llm_inferred: AudienceProfile) -> AudienceProfile:
    """Resolve final audience profile by honoring config lock and confidence threshold.

    Rule: if config is locked, always use locked segments with llm confidence.
    Rule: if unlocked and llm confidence < 0.55, fallback to locked segments.
    Otherwise use llm inferred segments.
    """
    if company_config.locked:
        return AudienceProfile(segments=company_config.locked_segments, confidence=llm_inferred.confidence)
    if llm_inferred.confidence < 0.55:
        return AudienceProfile(segments=company_config.locked_segments, confidence=0.55)
    return llm_inferred


def select_posting_time(ranked_windows: list[TimeWindow], context: ScheduleContext) -> TimeWindow:
    """Choose posting time from ranked windows with deterministic filtering.

    Rule: if force_window is true, return first ranked window regardless of confidence.
    Rule: otherwise return first window meeting minimum confidence.
    Fallback: if none meet threshold, return highest-confidence window.
    """
    if not ranked_windows:
        raise ValueError("ranked_windows cannot be empty")
    if context.force_window:
        return ranked_windows[0]
    for window in ranked_windows:
        if window.confidence >= context.minimum_confidence:
            return window
    return max(ranked_windows, key=lambda w: w.confidence)


def adapt_tone(base_fingerprint: ToneFingerprint, post_intent: PostIntent) -> ToneFingerprint:
    """Adapt tone values by post intent with bounded deterministic adjustments.

    Rule: each intent maps to fixed deltas; values are clamped to [0.0, 1.0].
    """
    deltas = {
        "announce": (0.05, 0.10, -0.05),
        "educate": (-0.05, 0.15, -0.10),
        "promote": (0.10, 0.05, 0.10),
        "engage": (0.10, -0.05, 0.15),
        "inspire": (0.15, -0.05, 0.20),
        "crisis_response": (-0.10, 0.20, -0.20),
    }
    dw, da, dp = deltas[post_intent]

    def clamp(v: float) -> float:
        return min(1.0, max(0.0, round(v, 4)))

    return ToneFingerprint(
        warmth=clamp(base_fingerprint.warmth + dw),
        authority=clamp(base_fingerprint.authority + da),
        playfulness=clamp(base_fingerprint.playfulness + dp),
    )


def route_platforms(request: PostRequest, profiles: dict[str, BrandProfile]) -> PlatformRoutingPlan:
    """Route platforms by explicit request and profile eligibility.

    Rule: retain only requested platforms with enabled profiles.
    Rule: for immediate urgency, cap selected platforms to first 3.
    Rule: if no eligible platform exists, raise ValueError.
    """
    selected = [p for p in request.target_platforms if profiles.get(p) and profiles[p].platform_enabled]
    if request.urgency_level == "immediate":
        selected = selected[:3]
    if not selected:
        raise ValueError("No eligible platforms for routing")
    return PlatformRoutingPlan(selected_platforms=selected)
