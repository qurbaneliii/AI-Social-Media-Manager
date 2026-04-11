# FILE: packages/decision-engine/functions/tone_adaptation.py
from __future__ import annotations

from packages.decision_engine.constants import (
    CRISIS_FORBIDDEN_CTA_TOKENS,
    CRISIS_REQUIRED_EMPATHY,
    INTENT_DELTAS,
    PLATFORM_TONE_MODIFIERS,
    TONE_MIN_AVG_SENTENCE_LENGTH,
    TONE_SCORE_MAX,
    TONE_SCORE_MIN,
)
from packages.decision_engine.models import PostIntent, ToneAdaptationInput, ToneAdaptationResult, ToneFingerprint


_SCORE_DIMENSIONS: tuple[str, ...] = (
    "formality",
    "humor",
    "assertiveness",
    "optimism",
    "clarity",
    "urgency",
    "warmth",
    "empathy",
    "storytelling",
)


def _clamp_score(value: int) -> int:
    return max(TONE_SCORE_MIN, min(TONE_SCORE_MAX, value))


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


def adapt_tone(input: ToneAdaptationInput) -> ToneAdaptationResult:
    """
    Implements Section 5.4 Tone Adaptation Logic.

    Decision made:
    Adapts a base tone fingerprint to post intent and platform constraints,
    then applies crisis-safe communication rules when relevant.

    Spec section:
    Section 5.4.

    Rule priority order:
    1. Copy base fingerprint into mutable working values.
    2. Apply intent deltas.
    3. Clamp score and emoji bounds.
    4. Apply platform-specific tone modifiers and clamp again.
    5. Apply crisis-response hard safety constraints.
    6. Return adaptation result including applied deltas/modifiers.

    Edge cases handled:
    - Any score over/under bounds is clamped and tracked.
    - Sentence length factor for X never drops below configured minimum.
    - Crisis CTA filtering handles both spaces and underscores.
    - Crisis forbidden terms are merged deterministically with de-duplication.
    """
    # 1. COPY BASE FINGERPRINT
    working = input.base_fingerprint.model_dump(mode="python")
    clamped_dimensions: list[str] = []

    # 2. APPLY INTENT DELTAS
    deltas = INTENT_DELTAS[str(input.post_intent)]
    applied_intent_deltas: dict[str, int] = {}

    for dimension, delta in deltas.items():
        applied_intent_deltas[dimension] = delta

        if dimension == "avg_sentence_length_target":
            working["avg_sentence_length_target"] = working["avg_sentence_length_target"] * (1 + (delta / 100))
            continue
        if dimension == "emoji_density_target":
            working["emoji_density_target"] = working["emoji_density_target"] + (delta / 100)
            continue

        score_key = f"{dimension}_score"
        if score_key in working:
            working[score_key] = int(working[score_key]) + delta

    # 3. CLAMP AFTER INTENT APPLICATION
    for dimension in _SCORE_DIMENSIONS:
        score_key = f"{dimension}_score"
        old_value = int(working[score_key])
        new_value = _clamp_score(old_value)
        if new_value != old_value and score_key not in clamped_dimensions:
            clamped_dimensions.append(score_key)
        working[score_key] = new_value

    working["emoji_density_target"] = max(0.0, min(1.0, float(working["emoji_density_target"])))

    # 4. APPLY PLATFORM MODIFIERS
    modifiers = PLATFORM_TONE_MODIFIERS.get(str(input.platform), {})
    applied_platform_modifiers: dict[str, int | float] = {}

    for dimension, modifier_value in modifiers.items():
        applied_platform_modifiers[dimension] = modifier_value

        if dimension == "sentence_length_factor":
            adjusted = float(working["avg_sentence_length_target"]) * (1 + float(modifier_value))
            working["avg_sentence_length_target"] = max(TONE_MIN_AVG_SENTENCE_LENGTH, adjusted)
            continue

        score_key = f"{dimension}_score"
        if score_key in working:
            old_value = int(working[score_key]) + int(modifier_value)
            new_value = _clamp_score(old_value)
            if new_value != old_value and score_key not in clamped_dimensions:
                clamped_dimensions.append(score_key)
            working[score_key] = new_value

    # 5. CRISIS RESPONSE SAFETY CONSTRAINTS
    crisis_mode_active = input.post_intent == PostIntent.crisis_response
    if crisis_mode_active:
        if CRISIS_REQUIRED_EMPATHY:
            empathy_rule = "Must include a sincere empathy statement in the opening."
            working["style_rules"] = [*working["style_rules"], empathy_rule]

        filtered_ctas: list[str] = []
        for cta in list(working["preferred_cta_types"]):
            normalized_cta = cta.lower().replace("_", " ")
            blocked = any(forbidden in normalized_cta for forbidden in CRISIS_FORBIDDEN_CTA_TOKENS)
            if not blocked:
                filtered_ctas.append(cta)

        if not filtered_ctas:
            filtered_ctas = ["learn_more", "comment"]
        working["preferred_cta_types"] = filtered_ctas

        merged_forbidden = [*working["forbidden_terms"], *CRISIS_FORBIDDEN_CTA_TOKENS]
        working["forbidden_terms"] = _dedupe_preserve_order(merged_forbidden)

    # 6. RETURN
    adapted = ToneFingerprint(**working)
    return ToneAdaptationResult(
        adapted_fingerprint=adapted,
        applied_intent_deltas=applied_intent_deltas,
        applied_platform_modifiers=applied_platform_modifiers,
        crisis_mode_active=crisis_mode_active,
        clamped_dimensions=clamped_dimensions,
    )
