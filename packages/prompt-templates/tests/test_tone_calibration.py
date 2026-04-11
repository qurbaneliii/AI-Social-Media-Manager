# FILE: packages/prompt-templates/tests/test_tone_calibration.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptVariableError
from packages.prompt_templates.context_models.tone_context import ToneContext
from packages.prompt_templates.templates import tone_calibration as tone_template
from packages.types.enums import Platform


def make_context() -> ToneContext:
    return ToneContext(
        company_id=uuid4(),
        company_name="Acme",
        tone_descriptors=["clear", "practical", "optimistic"],
        brand_positioning="We help lean marketing teams execute social strategy with confidence and consistency.",
        sample_posts=[
            {"text": "We simplified campaign planning for distributed teams this week.", "platform": Platform.linkedin, "engagement_rate": 0.12},
            {"text": "Build better social experiments with less coordination overhead.", "platform": Platform.linkedin, "engagement_rate": 0.11},
            {"text": "Your weekly reporting should take minutes, not hours.", "platform": Platform.facebook, "engagement_rate": 0.10},
            {"text": "Strong messaging starts with a repeatable workflow.", "platform": Platform.instagram, "engagement_rate": 0.09},
            {"text": "Operational clarity creates better campaign outcomes.", "platform": Platform.x, "engagement_rate": 0.08},
        ],
        approved_vocabulary=["workflow"],
        banned_vocabulary=["guaranteed", "effortless"],
    )


def valid_payload(confidence: float = 0.8) -> dict:
    return {
        "tone_fingerprint": {
            "formality_score": 62,
            "humor_score": 28,
            "assertiveness_score": 55,
            "optimism_score": 68,
            "emoji_density_target": 0.08,
            "avg_sentence_length_target": 14.0,
            "reading_level_target": "grade_9_to_12",
            "preferred_cta_types": ["learn_more"],
            "style_rules": ["Be concise", "Lead with value", "Avoid hype", "Use active voice", "Keep CTA specific"],
            "lexical_signature": {
                "top_keywords": [{"term": "workflow", "weight": 0.9}],
                "forbidden_terms": ["guaranteed"],
            },
            "intent_modifiers": {
                "announce": {"delta": {"formality": 2, "humor": -1, "assertiveness": 3}},
                "educate": {"delta": {"formality": 4, "humor": -2, "assertiveness": 1}},
                "promote": {"delta": {"formality": -1, "humor": 2, "assertiveness": 4}},
                "engage": {"delta": {"formality": -2, "humor": 4, "assertiveness": 0}},
                "inspire": {"delta": {"formality": 0, "humor": 2, "assertiveness": 2}},
                "crisis_response": {"delta": {"formality": 6, "humor": -5, "assertiveness": 5}},
            },
        },
        "confidence": confidence,
    }


def test_build_prompt_returns_two_messages() -> None:
    messages = tone_template.build_tone_calibration_prompt(make_context())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_all_variables_resolved() -> None:
    messages = tone_template.build_tone_calibration_prompt(make_context())
    assert "{{" not in messages[0]["content"] + messages[1]["content"]
    assert "}}" not in messages[0]["content"] + messages[1]["content"]


def test_missing_variable_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tone_template,
        "USER_PROMPT_TEMPLATE",
        tone_template.USER_PROMPT_TEMPLATE + "\nX={{MISSING_REQUIRED}}",
    )
    with pytest.raises(PromptVariableError):
        tone_template.build_tone_calibration_prompt(make_context())


def test_parse_valid_response() -> None:
    parsed = tone_template.parse_tone_calibration_response(json.dumps(valid_payload()), make_context())
    assert parsed.data.confidence == 0.8


def test_parse_malformed_json_triggers_repair() -> None:
    raw = f"```json\n{json.dumps(valid_payload())}\n```"
    parsed = tone_template.parse_tone_calibration_response(raw, make_context())
    assert parsed.was_repaired is True


def test_parse_unrecoverable_json_raises() -> None:
    with pytest.raises(ValueError):
        tone_template.parse_tone_calibration_response("garbage", make_context())


def test_parse_low_confidence_raises() -> None:
    with pytest.raises(ValueError):
        tone_template.parse_tone_calibration_response(json.dumps(valid_payload(confidence=0.4)), make_context())


def test_parse_missing_intent_modifier_key_raises() -> None:
    payload = valid_payload()
    del payload["tone_fingerprint"]["intent_modifiers"]["announce"]
    with pytest.raises(ValueError):
        tone_template.parse_tone_calibration_response(json.dumps(payload), make_context())


def test_parse_unexpected_intent_modifier_key_raises() -> None:
    payload = valid_payload()
    payload["tone_fingerprint"]["intent_modifiers"]["unexpected"] = {
        "delta": {"formality": 0, "humor": 0, "assertiveness": 0}
    }
    with pytest.raises(ValueError):
        tone_template.parse_tone_calibration_response(json.dumps(payload), make_context())


def test_parse_insufficient_style_rules_raises() -> None:
    payload = valid_payload()
    payload["tone_fingerprint"]["style_rules"] = ["short", "two", "three", "four"]
    with pytest.raises(ValueError):
        tone_template.parse_tone_calibration_response(json.dumps(payload), make_context())


def test_parse_missing_banned_vocab_in_forbidden_terms_auto_corrected() -> None:
    parsed = tone_template.parse_tone_calibration_response(json.dumps(valid_payload()), make_context())
    assert "effortless" in parsed.data.tone_fingerprint.lexical_signature.forbidden_terms
    assert parsed.was_repaired is True
