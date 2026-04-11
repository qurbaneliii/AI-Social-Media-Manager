# FILE: packages/decision-engine/tests/test_tone_adaptation.py
from __future__ import annotations

from packages.decision_engine.constants import CRISIS_FORBIDDEN_CTA_TOKENS
from packages.decision_engine.functions.tone_adaptation import adapt_tone
from packages.decision_engine.models import (
    Platform,
    PostIntent,
    ToneAdaptationInput,
    ToneFingerprint,
)


def _base_fingerprint(**overrides) -> ToneFingerprint:
    payload = {
        "formality_score": 50,
        "humor_score": 50,
        "assertiveness_score": 50,
        "optimism_score": 50,
        "emoji_density_target": 0.2,
        "avg_sentence_length_target": 15.0,
        "clarity_score": 50,
        "urgency_score": 50,
        "warmth_score": 50,
        "empathy_score": 50,
        "storytelling_score": 50,
        "preferred_cta_types": ["buy_now", "learn_more"],
        "style_rules": ["Use active voice."],
        "forbidden_terms": ["guaranteed"],
    }
    payload.update(overrides)
    return ToneFingerprint(**payload)


def _adapt(
    *,
    post_intent: PostIntent,
    platform: Platform,
    base: ToneFingerprint | None = None,
):
    return adapt_tone(
        ToneAdaptationInput(
            base_fingerprint=base or _base_fingerprint(),
            post_intent=post_intent,
            platform=platform,
        )
    )


def test_announce_intent_increases_formality():
    result = _adapt(post_intent=PostIntent.announce, platform=Platform.linkedin)
    assert result.adapted_fingerprint.formality_score == 66


def test_scores_clamped_at_100():
    base = _base_fingerprint(formality_score=95)
    result = _adapt(post_intent=PostIntent.announce, platform=Platform.instagram, base=base)

    assert result.adapted_fingerprint.formality_score == 100
    assert "formality_score" in result.clamped_dimensions


def test_scores_clamped_at_0():
    base = _base_fingerprint(humor_score=5)
    result = _adapt(post_intent=PostIntent.crisis_response, platform=Platform.instagram, base=base)

    assert result.adapted_fingerprint.humor_score == 0
    assert "humor_score" in result.clamped_dimensions


def test_linkedin_platform_adds_formality():
    base = _base_fingerprint(formality_score=50)
    result = _adapt(post_intent=PostIntent.announce, platform=Platform.linkedin, base=base)

    assert result.adapted_fingerprint.formality_score == 66


def test_tiktok_platform_adds_humor():
    base = _base_fingerprint(humor_score=50)
    result = _adapt(post_intent=PostIntent.engage, platform=Platform.tiktok, base=base)

    assert result.adapted_fingerprint.humor_score == 72


def test_x_platform_reduces_sentence_length():
    base = _base_fingerprint(avg_sentence_length_target=15.0)
    result = _adapt(post_intent=PostIntent.promote, platform=Platform.x, base=base)

    assert result.adapted_fingerprint.avg_sentence_length_target == 12.0


def test_crisis_response_removes_buy_now_cta():
    base = _base_fingerprint(preferred_cta_types=["buy_now", "learn_more"])
    result = _adapt(post_intent=PostIntent.crisis_response, platform=Platform.instagram, base=base)

    assert "buy_now" not in result.adapted_fingerprint.preferred_cta_types
    assert "learn_more" in result.adapted_fingerprint.preferred_cta_types


def test_crisis_response_adds_empathy_style_rule():
    result = _adapt(post_intent=PostIntent.crisis_response, platform=Platform.instagram)
    assert any("empathy" in rule.lower() for rule in result.adapted_fingerprint.style_rules)


def test_crisis_response_adds_forbidden_terms():
    result = _adapt(post_intent=PostIntent.crisis_response, platform=Platform.instagram)
    assert all(token in result.adapted_fingerprint.forbidden_terms for token in CRISIS_FORBIDDEN_CTA_TOKENS)


def test_crisis_mode_active_flag_set():
    result = _adapt(post_intent=PostIntent.crisis_response, platform=Platform.instagram)
    assert result.crisis_mode_active is True


def test_non_crisis_mode_active_flag_false():
    result = _adapt(post_intent=PostIntent.promote, platform=Platform.instagram)
    assert result.crisis_mode_active is False
