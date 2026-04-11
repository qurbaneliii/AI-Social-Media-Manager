# FILE: packages/decision-engine/functions/audience_resolution.py
from __future__ import annotations

from copy import deepcopy

from packages.decision_engine.constants import (
    AUDIENCE_AGE_OVERLAP_MIN_PERCENT,
    AUDIENCE_APPROVAL_MIN_CONFIDENCE,
    AUDIENCE_BASELINE_CONFIDENCE,
    AUDIENCE_CONFLICT_CODE_OVERRIDE,
    AUDIENCE_HIGH_CONF_WEIGHT_COMPANY,
    AUDIENCE_HIGH_CONF_WEIGHT_LLM,
    AUDIENCE_LLM_CONFIDENCE_HIGH_THRESHOLD,
    AUDIENCE_LOCATION_OVERLAP_MIN,
    AUDIENCE_LOW_CONF_WEIGHT_COMPANY,
    AUDIENCE_LOW_CONF_WEIGHT_LLM,
)
from packages.decision_engine.models import (
    AgeRange,
    AudienceProfile,
    AudienceResolutionInput,
    LocationSet,
)


def _lower_set(items: list[str]) -> set[str]:
    return {item.lower() for item in items}


def _apply_exclusions(items: list[str], exclusions: set[str]) -> list[str]:
    return [item for item in items if item.lower() not in exclusions]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _segment_lift_map(historical_top_segments: list[dict]) -> dict[str, float]:
    lift_map: dict[str, float] = {}
    for row in historical_top_segments:
        segment = str(row.get("segment", "")).strip()
        if not segment:
            continue
        lift = float(row.get("engagement_lift", 0.0))
        current = lift_map.get(segment.lower())
        if current is None or lift > current:
            lift_map[segment.lower()] = lift
    return lift_map


def _sort_by_lift(items: list[str], lift_map: dict[str, float]) -> list[str]:
    return sorted(items, key=lambda item: lift_map.get(item.lower(), float("-inf")), reverse=True)


def _move_to_front(items: list[str], segment: str) -> list[str]:
    lowered = segment.lower()
    idx = next((i for i, item in enumerate(items) if item.lower() == lowered), None)
    if idx is None:
        return items
    chosen = items[idx]
    rest = [item for i, item in enumerate(items) if i != idx]
    return [chosen, *rest]


def resolve_audience(input: AudienceResolutionInput) -> AudienceProfile:
    """
    Implements Section 5.2 Audience Selection Logic.

    Decision made:
    Resolves a final audience profile by combining company baseline constraints,
    LLM-inferred audience traits, compliance restrictions, and historical uplift.

    Spec section:
    Section 5.2.

    Rule priority order:
    1. Start from company baseline.
    2. Apply compliance/mandatory inclusion/exclusion constraints.
    3. Determine confidence-based company vs. LLM merge weights.
    4. Merge locations with overlap guardrails.
    5. Merge age ranges with conflict handling and optional approval gating.
    6. Merge psychographic lists by union and uplift-aware ordering.
    7. Re-apply historical uplift front-prioritization.
    8. Compute final confidence and approval state.
    9. Return resolved profile.

    Edge cases handled:
    - Empty union for location overlap avoids division by zero.
    - Age overlap safely handles zero-span ranges.
    - Exclusion rules remove restricted segments across all audience fields.
    - Mandatory inclusions are always re-introduced into interests.
    - Historical uplift ordering remains deterministic.
    """
    # 1. START WITH COMPANY BASELINE
    company = input.company_config
    llm = input.llm_inferred

    final_age_range = AgeRange(lower=company.age_range.lower, upper=company.age_range.upper)
    final_primary_locations = deepcopy(company.locations)
    final_secondary_locations: list[str] = []
    final_interests = deepcopy(company.interests)
    final_values: list[str] = []
    final_pain_points: list[str] = []
    final_psychographics: dict[str, list[str]] = {}
    final_requires_approval = False
    final_override_codes: list[str] = []
    final_llm_weight = 0.0

    # 2. APPLY COMPLIANCE CONSTRAINTS
    exclusions = _lower_set(company.compliance_restrictions + company.mandatory_exclusions)
    final_primary_locations = _apply_exclusions(final_primary_locations, exclusions)
    final_interests = _apply_exclusions(final_interests, exclusions)

    # 3. DETERMINE LLM WEIGHT BY CONFIDENCE
    if llm.confidence >= AUDIENCE_LLM_CONFIDENCE_HIGH_THRESHOLD:
        w_company = AUDIENCE_HIGH_CONF_WEIGHT_COMPANY
        w_llm = AUDIENCE_HIGH_CONF_WEIGHT_LLM
    else:
        w_company = AUDIENCE_LOW_CONF_WEIGHT_COMPANY
        w_llm = AUDIENCE_LOW_CONF_WEIGHT_LLM
    final_llm_weight = w_llm

    # 4. LOCATION MERGE
    company_locs = {loc for loc in final_primary_locations}
    llm_locs = {loc for loc in llm.locations.primary + llm.locations.secondary}
    overlap_score = len(company_locs & llm_locs) / max(len(company_locs | llm_locs), 1)

    llm_only = [loc for loc in (llm.locations.primary + llm.locations.secondary) if loc not in company_locs]
    if overlap_score >= AUDIENCE_LOCATION_OVERLAP_MIN:
        final_secondary_locations.extend(loc for loc in llm_only if loc.lower() not in exclusions)
    else:
        final_secondary_locations.extend([])

    # 5. AGE RANGE MERGE
    company_lower = company.age_range.lower
    company_upper = company.age_range.upper
    llm_lower = llm.age_range.lower
    llm_upper = llm.age_range.upper

    intersection_years = max(0, min(company_upper, llm_upper) - max(company_lower, llm_lower))
    company_span = company_upper - company_lower
    overlap_pct = (intersection_years / max(company_span, 1)) * 100

    if overlap_pct >= AUDIENCE_AGE_OVERLAP_MIN_PERCENT and intersection_years > 0:
        final_age_range = AgeRange(lower=max(company_lower, llm_lower), upper=min(company_upper, llm_upper))
    else:
        final_age_range = AgeRange(lower=company_lower, upper=company_upper)
        if AUDIENCE_CONFLICT_CODE_OVERRIDE not in final_override_codes:
            final_override_codes.append(AUDIENCE_CONFLICT_CODE_OVERRIDE)
        if w_llm >= AUDIENCE_HIGH_CONF_WEIGHT_LLM:
            final_requires_approval = True

    # 6. PSYCHOGRAPHIC MERGE
    lift_map = _segment_lift_map(input.historical_top_segments)

    merged_interests = _dedupe_preserve_order([*final_interests, *llm.interests])
    merged_values = _dedupe_preserve_order([*final_values, *llm.values])
    merged_pain_points = _dedupe_preserve_order([*final_pain_points, *llm.pain_points])

    final_interests = _sort_by_lift(merged_interests, lift_map)
    final_values = _sort_by_lift(merged_values, lift_map)
    final_pain_points = _sort_by_lift(merged_pain_points, lift_map)

    merged_psychographics: dict[str, list[str]] = {}
    for key, values in llm.psychographics.items():
        merged_psychographics[key] = _sort_by_lift(_dedupe_preserve_order(values), lift_map)
    final_psychographics = merged_psychographics

    # 2 (continued): mandatory exclusions over all merged fields and mandatory inclusions.
    final_secondary_locations = _apply_exclusions(_dedupe_preserve_order(final_secondary_locations), exclusions)
    final_interests = _apply_exclusions(final_interests, exclusions)
    final_values = _apply_exclusions(final_values, exclusions)
    final_pain_points = _apply_exclusions(final_pain_points, exclusions)
    final_psychographics = {
        key: _apply_exclusions(_dedupe_preserve_order(values), exclusions)
        for key, values in final_psychographics.items()
    }

    for required in company.mandatory_inclusions:
        if required.lower() not in _lower_set(final_interests):
            final_interests.append(required)

    # 7. APPLY HISTORY UPLIFT
    ordered_history = sorted(
        input.historical_top_segments,
        key=lambda row: float(row.get("engagement_lift", 0.0)),
    )
    for row in ordered_history:
        segment = str(row.get("segment", "")).strip()
        if not segment:
            continue
        final_interests = _move_to_front(final_interests, segment)
        final_pain_points = _move_to_front(final_pain_points, segment)

    # 8. CONFIDENCE AND APPROVAL
    if llm.confidence < AUDIENCE_APPROVAL_MIN_CONFIDENCE:
        final_requires_approval = True

    final_confidence = AUDIENCE_BASELINE_CONFIDENCE * w_company + llm.confidence * w_llm

    # 9. RETURN
    return AudienceProfile(
        age_range=final_age_range,
        locations=LocationSet(
            primary=_dedupe_preserve_order(final_primary_locations),
            secondary=_dedupe_preserve_order(final_secondary_locations),
        ),
        interests=_dedupe_preserve_order(final_interests),
        values=_dedupe_preserve_order(final_values),
        pain_points=_dedupe_preserve_order(final_pain_points),
        psychographics=final_psychographics,
        confidence=final_confidence,
        requires_approval=final_requires_approval,
        override_codes=_dedupe_preserve_order(final_override_codes),
        llm_contribution_weight=final_llm_weight,
    )
