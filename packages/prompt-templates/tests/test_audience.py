# FILE: packages/prompt-templates/tests/test_audience.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptVariableError
from packages.prompt_templates.context_models.audience_context import AudienceContext
from packages.prompt_templates.templates import audience as audience_template
from packages.types.enums import Platform, PostIntent


def make_context() -> AudienceContext:
    return AudienceContext(
        company_id=uuid4(),
        platforms=[Platform.facebook, Platform.linkedin],
        company_profile_json=json.dumps({"industry": "SaaS", "size": "SMB"}),
        post_intent=PostIntent.educate,
        content_topic="Campaign performance insights",
        value_prop="Actionable recommendations in minutes",
    )


def valid_payload(confidence: float = 0.8) -> dict:
    return {
        "primary_demographic": {
            "age_range": "25-44",
            "gender_split": {"female": 0.5, "male": 0.5},
        },
        "psychographic_profile": {"motivation": "efficiency"},
        "platform_segments": {
            "facebook_custom_audience": {"interests": ["marketing"]},
            "linkedin_audience_attributes": {"titles": ["Growth Lead"]},
            "x_interest_clusters": {"clusters": ["MarTech"]},
            "tiktok_interest_categories": {"categories": ["Business"]},
        },
        "natural_language_summary": "Primary audience are growth-minded marketing operators.",
        "confidence": confidence,
    }


def test_build_prompt_returns_two_messages() -> None:
    messages = audience_template.build_audience_targeting_prompt(make_context())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_all_variables_resolved() -> None:
    messages = audience_template.build_audience_targeting_prompt(make_context())
    assert "{{" not in messages[0]["content"] + messages[1]["content"]
    assert "}}" not in messages[0]["content"] + messages[1]["content"]


def test_missing_variable_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        audience_template,
        "USER_PROMPT_TEMPLATE",
        audience_template.USER_PROMPT_TEMPLATE + "\nX={{MISSING_REQUIRED}}",
    )
    with pytest.raises(PromptVariableError):
        audience_template.build_audience_targeting_prompt(make_context())


def test_parse_valid_response() -> None:
    parsed = audience_template.parse_audience_targeting_response(
        json.dumps(valid_payload()), make_context()
    )
    assert parsed.data.confidence == 0.8


def test_parse_malformed_json_triggers_repair() -> None:
    raw = f"```json\n{json.dumps(valid_payload())}\n```"
    parsed = audience_template.parse_audience_targeting_response(raw, make_context())
    assert parsed.was_repaired is True


def test_parse_unrecoverable_json_raises() -> None:
    with pytest.raises(ValueError):
        audience_template.parse_audience_targeting_response("bad-json", make_context())


def test_parse_gender_split_not_summing_to_one_raises() -> None:
    payload = valid_payload()
    payload["primary_demographic"]["gender_split"] = {"female": 0.8, "male": 0.4}
    with pytest.raises(ValueError):
        audience_template.parse_audience_targeting_response(json.dumps(payload), make_context())


def test_parse_gender_split_missing_object_raises() -> None:
    payload = valid_payload()
    payload["primary_demographic"]["gender_split"] = []
    with pytest.raises(ValueError):
        audience_template.parse_audience_targeting_response(json.dumps(payload), make_context())


def test_parse_invalid_age_range_raises() -> None:
    payload = valid_payload()
    payload["primary_demographic"]["age_range"] = "44-25"
    with pytest.raises(ValueError):
        audience_template.parse_audience_targeting_response(json.dumps(payload), make_context())


def test_parse_missing_platform_segment_key_raises() -> None:
    payload = valid_payload()
    del payload["platform_segments"]["x_interest_clusters"]
    with pytest.raises(ValueError):
        audience_template.parse_audience_targeting_response(json.dumps(payload), make_context())


def test_parse_low_confidence_sets_requires_approval() -> None:
    parsed = audience_template.parse_audience_targeting_response(
        json.dumps(valid_payload(confidence=0.5)), make_context()
    )
    assert parsed.metadata.get("requires_approval") is True
