# FILE: packages/prompt-templates/tests/test_seo.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptVariableError
from packages.prompt_templates.context_models.seo_context import SEOContext
from packages.prompt_templates.templates import seo as seo_template
from packages.prompt_templates.validators import validate_seo_prompt
from packages.types.enums import MarketSegment, Platform


def make_context() -> SEOContext:
    return SEOContext(
        company_id=uuid4(),
        post_caption="Enterprise modernization strategy for distributed GTM teams.",
        image_description="Team reviewing campaign dashboard",
        industry_vertical="MarTech",
        target_keywords=["marketing automation"],
        platform=Platform.linkedin,
        market_segment=MarketSegment.B2B,
        banned_vocabulary=["guaranteed"],
    )


def valid_payload() -> dict:
    return {
        "meta_title": "Marketing Automation Strategy",
        "meta_description": "Actionable guidance to improve campaign operations with automation.",
        "alt_text": "A growth team reviewing automation metrics on a dashboard.",
        "keywords": ["marketing automation", "campaign ops"],
        "keyword_density_targets": {"primary": 0.02, "secondary": 0.01},
    }


def test_build_prompt_returns_two_messages() -> None:
    messages = seo_template.build_seo_optimization_prompt(make_context())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_all_variables_resolved() -> None:
    messages = seo_template.build_seo_optimization_prompt(make_context())
    assert "{{" not in messages[0]["content"] + messages[1]["content"]
    assert "}}" not in messages[0]["content"] + messages[1]["content"]


def test_missing_variable_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        seo_template,
        "USER_PROMPT_TEMPLATE",
        seo_template.USER_PROMPT_TEMPLATE + "\nX={{MISSING_REQUIRED}}",
    )
    with pytest.raises(PromptVariableError):
        seo_template.build_seo_optimization_prompt(make_context())


def test_parse_valid_response() -> None:
    parsed = seo_template.parse_seo_optimization_response(json.dumps(valid_payload()), make_context())
    assert parsed.data.meta_title == "Marketing Automation Strategy"


def test_parse_malformed_json_triggers_repair() -> None:
    raw = f"```json\n{json.dumps(valid_payload())}\n```"
    parsed = seo_template.parse_seo_optimization_response(raw, make_context())
    assert parsed.was_repaired is True


def test_parse_unrecoverable_json_raises() -> None:
    with pytest.raises(ValueError):
        seo_template.parse_seo_optimization_response("nonsense", make_context())


def test_parse_meta_title_auto_truncated_within_margin() -> None:
    payload = valid_payload()
    payload["meta_title"] = "A" * 66
    parsed = seo_template.parse_seo_optimization_response(json.dumps(payload), make_context())
    assert len(parsed.data.meta_title) <= 60
    assert parsed.was_repaired is True


def test_parse_meta_title_auto_truncated_without_word_boundary() -> None:
    payload = valid_payload()
    payload["meta_title"] = "A" * 66
    parsed = seo_template.parse_seo_optimization_response(json.dumps(payload), make_context())
    assert parsed.data.meta_title == ("A" * 60)


def test_parse_meta_title_exceeding_margin_raises() -> None:
    payload = valid_payload()
    payload["meta_title"] = "B" * 80
    with pytest.raises(ValueError):
        seo_template.parse_seo_optimization_response(json.dumps(payload), make_context())


def test_parse_non_object_response_raises() -> None:
    with pytest.raises(ValueError):
        seo_template.parse_seo_optimization_response("[1,2,3]", make_context())


def test_parse_banned_vocab_in_metadata_raises() -> None:
    payload = valid_payload()
    payload["meta_description"] = "Guaranteed outcomes for every team."
    with pytest.raises(ValueError):
        seo_template.parse_seo_optimization_response(json.dumps(payload), make_context())


def test_flesch_warning_does_not_block_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    messages = seo_template.build_seo_optimization_prompt(make_context())
    monkeypatch.setattr("packages.prompt_templates.validators.textstat.flesch_reading_ease", lambda _: 10.0)
    assert validate_seo_prompt(messages, make_context()) is True
