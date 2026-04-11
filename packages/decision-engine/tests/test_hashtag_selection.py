# FILE: packages/decision-engine/tests/test_hashtag_selection.py
from __future__ import annotations

import math

import pytest

from packages.decision_engine.constants import (
    HASHTAG_QUOTA_BROAD,
    HASHTAG_QUOTA_MICRO,
    HASHTAG_QUOTA_NICHE,
    HASHTAG_UNDERFILL_SCORE_PENALTY,
)
from packages.decision_engine.functions.hashtag_selection import (
    cosine_similarity,
    normalize_performance,
    select_hashtags,
)
from packages.decision_engine.models import HashtagCandidate, HashtagSelectionInput, Platform


@pytest.fixture
def topic_embedding() -> list[float]:
    return [1.0, 0.0]


@pytest.fixture
def company_embedding() -> list[float]:
    return [1.0, 0.0]


@pytest.fixture
def make_candidate():
    def _make(
        tag: str,
        *,
        embedding: list[float] | None = None,
        monthly_volume: int,
        days_since_peak: int = 2,
        historical_engagement_uplift: float = 1.0,
        brand_alignment_score: float = 0.9,
        source: str = "llm",
    ) -> HashtagCandidate:
        return HashtagCandidate(
            tag=tag,
            embedding=embedding or [1.0, 0.0],
            monthly_volume=monthly_volume,
            days_since_peak=days_since_peak,
            historical_engagement_uplift=historical_engagement_uplift,
            brand_alignment_score=brand_alignment_score,
            source=source,
        )

    return _make


def _build_input(
    *,
    candidates_llm: list[HashtagCandidate],
    candidates_vector: list[HashtagCandidate],
    topic_embedding: list[float],
    company_embedding: list[float],
    banned_tags: list[str] | None = None,
    platform: Platform = Platform.instagram,
) -> HashtagSelectionInput:
    return HashtagSelectionInput(
        candidates_llm=candidates_llm,
        candidates_vector=candidates_vector,
        topic_embedding=topic_embedding,
        banned_tags=banned_tags or [],
        platform=platform,
        company_profile_embedding=company_embedding,
    )


def _all_tags(result) -> list[str]:
    return [*(entry.tag for entry in result.broad), *(entry.tag for entry in result.niche), *(entry.tag for entry in result.micro)]


def test_exact_quota_returned_when_sufficient_candidates(make_candidate, topic_embedding, company_embedding):
    broad = [
        make_candidate(f"broad_{i}", monthly_volume=700_000 + i, historical_engagement_uplift=2.0 + i / 10)
        for i in range(10)
    ]
    niche = [
        make_candidate(f"niche_{i}", monthly_volume=150_000 + i, historical_engagement_uplift=1.5 + i / 10)
        for i in range(10)
    ]
    micro = [
        make_candidate(f"micro_{i}", monthly_volume=30_000 + i, historical_engagement_uplift=1.2 + i / 10)
        for i in range(10)
    ]

    result = select_hashtags(
        _build_input(
            candidates_llm=[*broad, *niche],
            candidates_vector=micro,
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    assert len(result.broad) == HASHTAG_QUOTA_BROAD
    assert len(result.niche) == HASHTAG_QUOTA_NICHE
    assert len(result.micro) == HASHTAG_QUOTA_MICRO


def test_banned_tag_excluded_from_all_tiers(make_candidate, topic_embedding, company_embedding):
    duplicate_llm = make_candidate("#Forbidden-Tag", monthly_volume=120_000, historical_engagement_uplift=1.0, source="llm")
    duplicate_vector = make_candidate("forbidden_tag", monthly_volume=130_000, historical_engagement_uplift=2.0, source="vector")
    safe = make_candidate("allowed_tag", monthly_volume=120_000, historical_engagement_uplift=2.5)

    result = select_hashtags(
        _build_input(
            candidates_llm=[duplicate_llm, safe],
            candidates_vector=[duplicate_vector],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
            banned_tags=["forbidden_tag"],
        )
    )

    assert "forbidden_tag" not in _all_tags(result)


def test_relevance_below_threshold_rejected(make_candidate, topic_embedding, company_embedding):
    low_rel = make_candidate(
        "low_rel",
        embedding=[0.0, 1.0],
        monthly_volume=120_000,
        historical_engagement_uplift=5.0,
    )
    good = make_candidate("good_niche", monthly_volume=120_000, historical_engagement_uplift=2.0)

    result = select_hashtags(
        _build_input(
            candidates_llm=[low_rel, good],
            candidates_vector=[],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    assert "low_rel" not in _all_tags(result)


def test_recency_below_threshold_rejected(make_candidate, topic_embedding, company_embedding):
    stale = make_candidate(
        "stale_tag",
        monthly_volume=120_000,
        days_since_peak=200,
        historical_engagement_uplift=5.0,
    )
    good = make_candidate("good_tag", monthly_volume=120_000, historical_engagement_uplift=2.0)

    assert math.exp(-200 / 30) < 0.20

    result = select_hashtags(
        _build_input(
            candidates_llm=[stale, good],
            candidates_vector=[],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    assert "stale_tag" not in _all_tags(result)


def test_score_below_threshold_rejected(make_candidate, topic_embedding, company_embedding):
    low_score = make_candidate(
        "low_score",
        embedding=[0.62, math.sqrt(1 - 0.62**2)],
        monthly_volume=120_000,
        days_since_peak=47,
        historical_engagement_uplift=-1.0,
        brand_alignment_score=0.0,
    )
    high = make_candidate("high_score", monthly_volume=120_000, historical_engagement_uplift=5.0)

    result = select_hashtags(
        _build_input(
            candidates_llm=[low_score, high],
            candidates_vector=[],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    assert "low_score" not in _all_tags(result)


def test_underfill_borrows_from_adjacent_tier_with_penalty(make_candidate, topic_embedding, company_embedding):
    broad = [
        make_candidate(f"broad_{i}", monthly_volume=700_000 + i, historical_engagement_uplift=5.0 + i)
        for i in range(2)
    ]
    niche = [
        make_candidate(f"niche_{i}", monthly_volume=120_000 + i, historical_engagement_uplift=float(i))
        for i in range(6)
    ]

    all_candidates = [*broad, *niche]
    result = select_hashtags(
        _build_input(
            candidates_llm=all_candidates,
            candidates_vector=[],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    borrowed = [entry for entry in result.broad if entry.source == "borrowed"]
    assert borrowed, "Expected at least one borrowed entry in broad tier"

    borrowed_tag = borrowed[0].tag
    borrowed_candidate = next(candidate for candidate in niche if candidate.tag == borrowed_tag)
    uplifts = [candidate.historical_engagement_uplift for candidate in all_candidates]
    raw_score = (
        0.35 * cosine_similarity(borrowed_candidate.embedding, topic_embedding)
        + 0.35 * normalize_performance(uplifts, borrowed_candidate.historical_engagement_uplift)
        + 0.20 * math.exp(-borrowed_candidate.days_since_peak / 30)
        + 0.10 * cosine_similarity(borrowed_candidate.embedding, company_embedding)
    )

    assert borrowed[0].score == pytest.approx(raw_score - HASHTAG_UNDERFILL_SCORE_PENALTY)


def test_platform_cap_enforced_correctly(make_candidate, topic_embedding, company_embedding):
    broad = [
        make_candidate(f"broad_cap_{i}", monthly_volume=700_000 + i, historical_engagement_uplift=2.0 + i / 10)
        for i in range(8)
    ]
    niche = [
        make_candidate(f"niche_cap_{i}", monthly_volume=120_000 + i, historical_engagement_uplift=2.0 + i / 10)
        for i in range(8)
    ]
    micro = [
        make_candidate(f"micro_cap_{i}", monthly_volume=30_000 + i, historical_engagement_uplift=2.0 + i / 10)
        for i in range(8)
    ]

    result = select_hashtags(
        _build_input(
            candidates_llm=[*broad, *niche],
            candidates_vector=micro,
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
            platform=Platform.x,
        )
    )

    assert len(result.broad) + len(result.niche) + len(result.micro) <= 3
    assert result.platform_cap_enforced is True


def test_deduplication_keeps_higher_uplift_candidate(make_candidate, topic_embedding, company_embedding):
    low = make_candidate("#SameTag", monthly_volume=120_000, historical_engagement_uplift=1.0, source="llm")
    high = make_candidate("same_tag", monthly_volume=120_000, historical_engagement_uplift=5.0, source="vector")

    result = select_hashtags(
        _build_input(
            candidates_llm=[low],
            candidates_vector=[high],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    same_tag_entries = [entry for entry in _all_tags(result) if entry == "same_tag"]
    assert len(same_tag_entries) == 1


def test_tier_relevance_threshold_prevents_wrong_tier_assignment(make_candidate, topic_embedding, company_embedding):
    high_volume_but_low_relevance = make_candidate(
        "big_but_low_rel",
        embedding=[0.63, math.sqrt(1 - 0.63**2)],
        monthly_volume=700_000,
        historical_engagement_uplift=5.0,
    )
    supportive = make_candidate("supportive_niche", monthly_volume=120_000, historical_engagement_uplift=6.0)

    result = select_hashtags(
        _build_input(
            candidates_llm=[high_volume_but_low_relevance, supportive],
            candidates_vector=[],
            topic_embedding=topic_embedding,
            company_embedding=company_embedding,
        )
    )

    assert "big_but_low_rel" not in [entry.tag for entry in result.broad]
    assert "big_but_low_rel" not in _all_tags(result)


def test_cosine_similarity_zero_vectors_returns_zero():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
