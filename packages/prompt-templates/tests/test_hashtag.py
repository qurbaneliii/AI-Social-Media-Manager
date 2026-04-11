# FILE: packages/prompt-templates/tests/test_hashtag.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptVariableError
from packages.prompt_templates.context_models.hashtag_context import HashtagContext
from packages.prompt_templates.templates import hashtag as hashtag_template


def make_context() -> HashtagContext:
    return HashtagContext(
        company_id=uuid4(),
        platform="instagram",
        post_topic="Practical social campaign automation tips",
        industry_vertical="MarTech",
        audience_summary="Growth teams in SMB SaaS",
        brand_positioning="Reliable AI support for marketers",
        trending_context=["automation week", "growth stack"],
        historical_tags=["#marketing", "#automation"],
        banned_tags=["#forbidden"],
    )


def valid_payload() -> dict:
    return {
        "broad": [
            {"tag": "#marketing", "reason": "high search"},
            {"tag": "#startup", "reason": "broad interest"},
            {"tag": "#growth", "reason": "category fit"},
        ],
        "niche": [
            {"tag": "#saasmarketing", "reason": "audience fit"},
            {"tag": "#campaignops", "reason": "topic fit"},
            {"tag": "#socialautomation", "reason": "intent fit"},
            {"tag": "#pipelinegrowth", "reason": "engagement history"},
            {"tag": "#acquisitionops", "reason": "niche relevance"},
        ],
        "micro": [
            {"tag": "#b2bgrowthops", "reason": "micro fit"},
            {"tag": "#demandgenlab", "reason": "micro fit"},
            {"tag": "#contentopsai", "reason": "micro fit"},
            {"tag": "#revopsplaybook", "reason": "micro fit"},
            {"tag": "#funnelcraft", "reason": "micro fit"},
        ],
    }


def test_build_prompt_returns_two_messages() -> None:
    messages = hashtag_template.build_hashtag_generation_prompt(make_context())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_all_variables_resolved() -> None:
    messages = hashtag_template.build_hashtag_generation_prompt(make_context())
    assert "{{" not in messages[0]["content"] + messages[1]["content"]
    assert "}}" not in messages[0]["content"] + messages[1]["content"]


def test_missing_variable_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        hashtag_template,
        "USER_PROMPT_TEMPLATE",
        hashtag_template.USER_PROMPT_TEMPLATE + "\nX={{MISSING_REQUIRED}}",
    )
    with pytest.raises(PromptVariableError):
        hashtag_template.build_hashtag_generation_prompt(make_context())


def test_parse_valid_response() -> None:
    parsed = hashtag_template.parse_hashtag_generation_response(
        json.dumps(valid_payload()), make_context()
    )
    assert len(parsed.data.broad) == 3


def test_parse_malformed_json_triggers_repair() -> None:
    raw = f"```json\n{json.dumps(valid_payload())}\n```"
    parsed = hashtag_template.parse_hashtag_generation_response(raw, make_context())
    assert parsed.was_repaired is True


def test_parse_unrecoverable_json_raises() -> None:
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response("bad-json", make_context())


def test_parse_wrong_tier_count_raises() -> None:
    payload = valid_payload()
    payload["broad"] = payload["broad"][:2]
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())


def test_parse_duplicate_tag_across_tiers_raises() -> None:
    payload = valid_payload()
    payload["micro"][0]["tag"] = "#marketing"
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())


def test_parse_banned_tag_removed_from_result() -> None:
    payload = valid_payload()
    payload["broad"][0]["tag"] = "#forbidden"
    parsed = hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())
    all_tags = [x.tag for x in parsed.data.broad + parsed.data.niche + parsed.data.micro]
    assert "#forbidden" not in all_tags


def test_parse_banned_tag_removed_from_niche_and_micro() -> None:
    payload = valid_payload()
    payload["niche"][0]["tag"] = "#forbidden"
    payload["micro"][0]["tag"] = "#forbidden2"
    context = make_context().model_copy(update={"banned_tags": ["#forbidden", "#forbidden2"]})
    parsed = hashtag_template.parse_hashtag_generation_response(json.dumps(payload), context)
    assert parsed.metadata["deficits"]["niche"] == 1
    assert parsed.metadata["deficits"]["micro"] == 1


def test_parse_invalid_hashtag_format_raises() -> None:
    payload = valid_payload()
    payload["broad"][0]["tag"] = "#InvalidTag"
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())


def test_parse_invalid_hashtag_without_hash_raises() -> None:
    payload = valid_payload()
    payload["broad"][0]["tag"] = "invalid"
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())


def test_parse_invalid_hashtag_with_space_raises() -> None:
    payload = valid_payload()
    payload["broad"][0]["tag"] = "#bad tag"
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())


def test_parse_invalid_hashtag_too_long_raises() -> None:
    payload = valid_payload()
    payload["broad"][0]["tag"] = "#" + ("a" * 50)
    with pytest.raises(ValueError):
        hashtag_template.parse_hashtag_generation_response(json.dumps(payload), make_context())
