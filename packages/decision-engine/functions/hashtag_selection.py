# FILE: packages/decision-engine/functions/hashtag_selection.py
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from packages.decision_engine.constants import (
    HASHTAG_BROAD_RELEVANCE_MIN,
    HASHTAG_BROAD_VOLUME_MIN,
    HASHTAG_MICRO_RELEVANCE_MIN,
    HASHTAG_MICRO_VOLUME_MAX,
    HASHTAG_NICHE_RELEVANCE_MIN,
    HASHTAG_NICHE_VOLUME_MAX,
    HASHTAG_NICHE_VOLUME_MIN,
    HASHTAG_PLATFORM_CAPS,
    HASHTAG_QUOTA_BROAD,
    HASHTAG_QUOTA_MICRO,
    HASHTAG_QUOTA_NICHE,
    HASHTAG_RECENCY_DECAY_DAYS,
    HASHTAG_RECENCY_THRESHOLD,
    HASHTAG_RELEVANCE_THRESHOLD,
    HASHTAG_SCORE_THRESHOLD,
    HASHTAG_UNDERFILL_SCORE_PENALTY,
    HASHTAG_WEIGHT_BRAND_FIT,
    HASHTAG_WEIGHT_PERFORMANCE,
    HASHTAG_WEIGHT_RECENCY,
    HASHTAG_WEIGHT_RELEVANCE,
)
from packages.decision_engine.models import (
    HashtagCandidate,
    HashtagEntry,
    HashtagSelectionInput,
    HashtagSet,
)


@dataclass(frozen=True)
class _ScoredCandidate:
    candidate: HashtagCandidate
    normalized_tag: str
    relevance: float
    performance: float
    recency: float
    brand_fit: float
    score: float


def _normalize_tag(tag: str) -> str:
    token = tag.lower().lstrip("#")
    return re.sub(r"[^a-z0-9_]", "", token)


def _entry_from_scored(
    scored: _ScoredCandidate,
    tier: str,
    source: str | None = None,
    score_penalty: float = 0.0,
) -> HashtagEntry:
    return HashtagEntry(
        tag=scored.normalized_tag,
        score=scored.score - score_penalty,
        tier=tier,
        source=source or scored.candidate.source,
    )


def _select_top(entries: list[_ScoredCandidate], quota: int, tier: str) -> list[HashtagEntry]:
    ranked = sorted(entries, key=lambda item: item.score, reverse=True)
    return [_entry_from_scored(item, tier=tier) for item in ranked[:quota]]


def _borrow_candidates(
    destination_tier: str,
    selected_tag_set: set[str],
    destination_entries: list[HashtagEntry],
    destination_quota: int,
    source_scored_candidates: list[_ScoredCandidate],
) -> list[HashtagEntry]:
    if len(destination_entries) >= destination_quota:
        return destination_entries

    ranked = sorted(source_scored_candidates, key=lambda item: item.score, reverse=True)
    updated = list(destination_entries)
    for candidate in ranked:
        if len(updated) >= destination_quota:
            break
        if candidate.normalized_tag in selected_tag_set:
            continue
        borrowed = _entry_from_scored(
            candidate,
            tier=destination_tier,
            source="borrowed",
            score_penalty=HASHTAG_UNDERFILL_SCORE_PENALTY,
        )
        updated.append(borrowed)
        selected_tag_set.add(candidate.normalized_tag)
    return updated


def select_hashtags(input: HashtagSelectionInput) -> HashtagSet:
    """
    Implements Section 5.1 Hashtag Selection Logic.

    Decision made:
    Selects, scores, tiers, and constrains hashtags into broad/niche/micro outputs.

    Spec section:
    Section 5.1.

    Rule priority order:
    1. Merge candidate pools.
    2. Normalize and deduplicate by normalized tag (keep higher uplift).
    3. Filter banned tags.
    4. Score candidates (relevance/performance/recency/brand fit weighted blend).
    5. Apply hard rejection thresholds.
    6. Assign tier by volume + tier-specific relevance checks.
    7. Select top per tier quota.
    8. Borrow from adjacent tiers with penalty when underfilled.
    9. Enforce platform total hashtag cap.
    10. Return final HashtagSet.

    Edge cases handled:
    - Empty vectors or zero vectors produce cosine similarity 0.0.
    - Empty company profile embedding falls back to pre-computed brand_alignment_score.
    - Equal uplifts in normalization return 0.5.
    - Deduplication preserves highest-uplift duplicate.
    - Borrowing never duplicates a tag already selected in another tier.
    - Platform cap trimming removes lowest micro first, then niche, then broad.
    """
    # 1. MERGE
    merged: list[HashtagCandidate] = [*input.candidates_llm, *input.candidates_vector]

    # 2. NORMALIZE AND DEDUPLICATE
    deduped: dict[str, HashtagCandidate] = {}
    for candidate in merged:
        normalized = _normalize_tag(candidate.tag)
        if not normalized:
            continue
        existing = deduped.get(normalized)
        if existing is None or (
            candidate.historical_engagement_uplift > existing.historical_engagement_uplift
        ):
            deduped[normalized] = candidate

    # 3. BANNED TAG FILTER
    banned = {_normalize_tag(tag) for tag in input.banned_tags}
    filtered: list[tuple[str, HashtagCandidate]] = [
        (tag, candidate)
        for tag, candidate in deduped.items()
        if tag and tag not in banned
    ]

    # 4. SCORING
    all_uplifts = [candidate.historical_engagement_uplift for _, candidate in filtered]
    scored: list[_ScoredCandidate] = []
    for normalized_tag, candidate in filtered:
        relevance = cosine_similarity(candidate.embedding, input.topic_embedding)
        performance = normalize_performance(all_uplifts, candidate.historical_engagement_uplift)
        recency = math.exp(-candidate.days_since_peak / HASHTAG_RECENCY_DECAY_DAYS)
        brand_fit = (
            cosine_similarity(candidate.embedding, input.company_profile_embedding)
            if input.company_profile_embedding
            else candidate.brand_alignment_score
        )
        score = (
            HASHTAG_WEIGHT_RELEVANCE * relevance
            + HASHTAG_WEIGHT_PERFORMANCE * performance
            + HASHTAG_WEIGHT_RECENCY * recency
            + HASHTAG_WEIGHT_BRAND_FIT * brand_fit
        )
        scored.append(
            _ScoredCandidate(
                candidate=candidate,
                normalized_tag=normalized_tag,
                relevance=relevance,
                performance=performance,
                recency=recency,
                brand_fit=brand_fit,
                score=score,
            )
        )

    # 5. THRESHOLD FILTERS
    eligible: list[_ScoredCandidate] = []
    for candidate in scored:
        if candidate.relevance < HASHTAG_RELEVANCE_THRESHOLD:
            continue
        if candidate.score < HASHTAG_SCORE_THRESHOLD:
            continue
        if candidate.recency < HASHTAG_RECENCY_THRESHOLD:
            continue
        eligible.append(candidate)

    # 6. TIER ASSIGNMENT
    broad_bucket: list[_ScoredCandidate] = []
    niche_bucket: list[_ScoredCandidate] = []
    micro_bucket: list[_ScoredCandidate] = []

    for candidate in eligible:
        volume = candidate.candidate.monthly_volume
        if volume >= HASHTAG_BROAD_VOLUME_MIN and candidate.relevance >= HASHTAG_BROAD_RELEVANCE_MIN:
            broad_bucket.append(candidate)
            continue
        if (
            HASHTAG_NICHE_VOLUME_MIN
            <= volume
            <= HASHTAG_NICHE_VOLUME_MAX
            and candidate.relevance >= HASHTAG_NICHE_RELEVANCE_MIN
        ):
            niche_bucket.append(candidate)
            continue
        if volume <= HASHTAG_MICRO_VOLUME_MAX and candidate.relevance >= HASHTAG_MICRO_RELEVANCE_MIN:
            micro_bucket.append(candidate)

    # 7. TIER SELECTION
    broad = _select_top(broad_bucket, HASHTAG_QUOTA_BROAD, "broad")
    niche = _select_top(niche_bucket, HASHTAG_QUOTA_NICHE, "niche")
    micro = _select_top(micro_bucket, HASHTAG_QUOTA_MICRO, "micro")

    # 8. UNDERFILL HANDLING
    underfilled_tiers: list[str] = []
    selected_tags: set[str] = {
        *(item.tag for item in broad),
        *(item.tag for item in niche),
        *(item.tag for item in micro),
    }

    if len(broad) < HASHTAG_QUOTA_BROAD:
        underfilled_tiers.append("broad")
        broad = _borrow_candidates(
            destination_tier="broad",
            selected_tag_set=selected_tags,
            destination_entries=broad,
            destination_quota=HASHTAG_QUOTA_BROAD,
            source_scored_candidates=niche_bucket,
        )

    if len(niche) < HASHTAG_QUOTA_NICHE:
        underfilled_tiers.append("niche")
        adjacent_pool = [*broad_bucket, *micro_bucket]
        niche = _borrow_candidates(
            destination_tier="niche",
            selected_tag_set=selected_tags,
            destination_entries=niche,
            destination_quota=HASHTAG_QUOTA_NICHE,
            source_scored_candidates=adjacent_pool,
        )

    if len(micro) < HASHTAG_QUOTA_MICRO:
        underfilled_tiers.append("micro")
        micro = _borrow_candidates(
            destination_tier="micro",
            selected_tag_set=selected_tags,
            destination_entries=micro,
            destination_quota=HASHTAG_QUOTA_MICRO,
            source_scored_candidates=niche_bucket,
        )

    # 9. PLATFORM CAP ENFORCEMENT
    platform_cap_enforced = False
    cap = HASHTAG_PLATFORM_CAPS[str(input.platform)]

    while len(broad) + len(niche) + len(micro) > cap:
        platform_cap_enforced = True
        if micro:
            min_index = min(range(len(micro)), key=lambda i: micro[i].score)
            micro.pop(min_index)
            continue
        if niche:
            min_index = min(range(len(niche)), key=lambda i: niche[i].score)
            niche.pop(min_index)
            continue
        if broad:
            min_index = min(range(len(broad)), key=lambda i: broad[i].score)
            broad.pop(min_index)
            continue
        break

    # 10. RETURN
    return HashtagSet(
        broad=broad,
        niche=niche,
        micro=micro,
        platform_cap_enforced=platform_cap_enforced,
        underfilled_tiers=underfilled_tiers,
    )


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns 0.0 when either vector is empty, dimensions differ, or either norm is zero.
    """
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def normalize_performance(uplifts: list[float], target: float) -> float:
    """
    Min-max normalize target uplift value within the full candidate-set uplift range.

    Returns 0.5 when no uplifts are present or all values are equal.
    """
    if not uplifts:
        return 0.5
    min_uplift = min(uplifts)
    max_uplift = max(uplifts)
    if min_uplift == max_uplift:
        return 0.5
    return (target - min_uplift) / (max_uplift - min_uplift)
