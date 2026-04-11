# FILE: packages/decision-engine/tests/test_audience_resolution.py
from __future__ import annotations

import pytest

from packages.decision_engine.constants import AUDIENCE_CONFLICT_CODE_OVERRIDE
from packages.decision_engine.functions.audience_resolution import resolve_audience
from packages.decision_engine.models import (
    AgeRange,
    AudienceConfig,
    AudienceProfile,
    AudienceResolutionInput,
    LocationSet,
    PostIntent,
)


@pytest.fixture
def company_config() -> AudienceConfig:
    return AudienceConfig(
        age_range=AgeRange(lower=25, upper=45),
        locations=["US", "UK"],
        interests=["automation", "analytics"],
        mandatory_inclusions=[],
        mandatory_exclusions=[],
        compliance_restrictions=[],
    )


def _llm_profile(
    *,
    confidence: float,
    age_lower: int = 30,
    age_upper: int = 55,
    locations_primary: list[str] | None = None,
    locations_secondary: list[str] | None = None,
    interests: list[str] | None = None,
    values: list[str] | None = None,
    pain_points: list[str] | None = None,
) -> AudienceProfile:
    return AudienceProfile(
        age_range=AgeRange(lower=age_lower, upper=age_upper),
        locations=LocationSet(
            primary=locations_primary or ["US", "CA"],
            secondary=locations_secondary or [],
        ),
        interests=interests or ["content_ops", "automation"],
        values=values or ["trust"],
        pain_points=pain_points or ["limited_team_bandwidth"],
        psychographics={"motivations": ["efficiency"]},
        confidence=confidence,
        requires_approval=False,
        override_codes=[],
        llm_contribution_weight=0.0,
    )


def _input(
    company_config: AudienceConfig,
    llm_inferred: AudienceProfile,
    historical_top_segments: list[dict] | None = None,
) -> AudienceResolutionInput:
    return AudienceResolutionInput(
        company_config=company_config,
        llm_inferred=llm_inferred,
        historical_top_segments=historical_top_segments or [],
        post_intent=PostIntent.engage,
    )


def test_high_confidence_llm_applies_45_weight(company_config):
    result = resolve_audience(_input(company_config, _llm_profile(confidence=0.80)))
    assert result.llm_contribution_weight == pytest.approx(0.45)


def test_low_confidence_llm_applies_20_weight(company_config):
    result = resolve_audience(_input(company_config, _llm_profile(confidence=0.60)))
    assert result.llm_contribution_weight == pytest.approx(0.20)


def test_compliance_restriction_always_applied(company_config):
    cfg = company_config.model_copy(
        update={
            "mandatory_exclusions": ["minors_segment"],
        }
    )
    llm = _llm_profile(confidence=0.80, interests=["minors_segment", "automation"])

    result = resolve_audience(_input(cfg, llm))
    assert "minors_segment" not in result.interests


def test_location_overlap_above_threshold_adds_llm_secondary(company_config):
    llm_low = _llm_profile(confidence=0.80, locations_primary=["US", "CA"])
    low_result = resolve_audience(_input(company_config, llm_low))
    assert low_result.locations.secondary == []

    cfg_high = company_config.model_copy(update={"locations": ["US", "UK", "CA"]})
    llm_high = _llm_profile(confidence=0.80, locations_primary=["US", "CA", "AU"])
    high_result = resolve_audience(_input(cfg_high, llm_high))
    assert high_result.locations.secondary == ["AU"]


def test_age_range_intersection_used_when_overlap_sufficient(company_config):
    llm = _llm_profile(confidence=0.80, age_lower=30, age_upper=55)
    result = resolve_audience(_input(company_config, llm))

    assert result.age_range.lower == 30
    assert result.age_range.upper == 45


def test_age_range_company_kept_when_overlap_insufficient(company_config):
    cfg = company_config.model_copy(update={"age_range": AgeRange(lower=18, upper=30)})
    llm = _llm_profile(confidence=0.80, age_lower=45, age_upper=65)

    result = resolve_audience(_input(cfg, llm))

    assert result.age_range.lower == 18
    assert result.age_range.upper == 30
    assert AUDIENCE_CONFLICT_CODE_OVERRIDE in result.override_codes


def test_interests_union_sorted_by_uplift(company_config):
    llm = _llm_profile(confidence=0.80, interests=["automation", "creator_marketing"])
    historical = [
        {"segment": "creator_marketing", "engagement_lift": 2.0},
        {"segment": "automation", "engagement_lift": 1.1},
    ]

    result = resolve_audience(_input(company_config, llm, historical))
    assert result.interests[0] == "creator_marketing"


def test_very_low_confidence_sets_requires_approval(company_config):
    result = resolve_audience(_input(company_config, _llm_profile(confidence=0.40)))
    assert result.requires_approval is True


def test_mandatory_inclusions_always_in_final_interests(company_config):
    cfg = company_config.model_copy(update={"mandatory_inclusions": ["enterprise_security"]})
    llm = _llm_profile(confidence=0.80, interests=["automation"])

    result = resolve_audience(_input(cfg, llm))
    assert "enterprise_security" in result.interests
