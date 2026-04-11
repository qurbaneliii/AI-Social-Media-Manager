# FILE: packages/prompt-templates/tests/test_caption.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptVariableError
from packages.prompt_templates.context_models.caption_context import CaptionContext
from packages.prompt_templates.templates import caption as caption_template
from packages.types.enums import Platform, PostIntent


def make_context() -> CaptionContext:
    return CaptionContext(
        company_id=uuid4(),
        company_name="Acme",
        company_positioning="AI-first social media automation",
        tone_fingerprint={"formality": 0.7},
        approved_vocabulary_list=["automation"],
        banned_vocabulary_list=["guaranteed"],
        post_intent=PostIntent.promote,
        core_message="Launch your campaign faster with intelligent optimization.",
        campaign_tag="launch_q2",
        cta_requirements=["learn_more"],
        visual_context_summary="Bright product UI screenshot",
        image_ocr_text="Try now",
        visual_tone_scores={"confidence": 0.8},
        audience_profile={"segment": "marketers"},
        seo_keywords=["social automation"],
        secondary_keywords=["campaign ops"],
        target_platforms=[Platform.instagram],
        platform_constraints=[
            {
                "platform": Platform.instagram,
                "max_chars": 2200,
                "supports_hashtags": True,
                "supports_links": False,
                "supports_emojis": True,
            }
        ],
    )


def test_build_prompt_returns_two_messages() -> None:
    messages = caption_template.build_caption_generation_prompt(make_context())
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_all_variables_resolved() -> None:
    messages = caption_template.build_caption_generation_prompt(make_context())
    assert "{{" not in messages[0]["content"] + messages[1]["content"]
    assert "}}" not in messages[0]["content"] + messages[1]["content"]


def test_missing_variable_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        caption_template,
        "USER_PROMPT_TEMPLATE",
        caption_template.USER_PROMPT_TEMPLATE + "\nMissing={{MISSING_REQUIRED}}",
    )
    with pytest.raises(PromptVariableError):
        caption_template.build_caption_generation_prompt(make_context())


def test_parse_valid_response() -> None:
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "Boost results with smarter campaign automation.",
                    "char_count": 47,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v2",
                    "text": "Launch campaigns quickly and scale your workflow.",
                    "char_count": 47,
                    "contains_cta": True,
                    "included_keywords": ["campaign ops"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v3",
                    "text": "Automate your social strategy and move faster.",
                    "char_count": 45,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
            ]
        }
    )
    parsed = caption_template.parse_caption_generation_response(raw, make_context())
    assert parsed.data.variants[0].platform == Platform.instagram


def test_caption_raw_response_without_context_parses() -> None:
    raw = '{"variants": []}'
    model = caption_template.CaptionRawResponse.model_validate_json(raw)
    assert model.variants == []


def test_parse_malformed_json_triggers_repair() -> None:
    payload = '{"variants":[{"platform":"instagram","variant_id":"v1","text":"A great caption","char_count":14,"contains_cta":true,"included_keywords":["social automation"]},{"platform":"instagram","variant_id":"v2","text":"Another caption","char_count":15,"contains_cta":true,"included_keywords":["campaign ops"]},{"platform":"instagram","variant_id":"v3","text":"Final caption","char_count":13,"contains_cta":true,"included_keywords":["social automation"]}]}'
    raw = f"```json\n{payload}\n```"
    parsed = caption_template.parse_caption_generation_response(raw, make_context())
    assert parsed.was_repaired is True


def test_parse_unrecoverable_json_raises() -> None:
    with pytest.raises(ValueError):
        caption_template.parse_caption_generation_response("not-json-at-all", make_context())


def test_parse_banned_vocab_in_variant_raises() -> None:
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "This is guaranteed to win.",
                    "char_count": 26,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v2",
                    "text": "Clean variant",
                    "char_count": 13,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v3",
                    "text": "Clean variant two",
                    "char_count": 17,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
            ]
        }
    )
    with pytest.raises(ValueError):
        caption_template.parse_caption_generation_response(raw, make_context())


def test_parse_char_count_mismatch_auto_corrected() -> None:
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "Correct me",
                    "char_count": 99,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v2",
                    "text": "Second variant",
                    "char_count": 14,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v3",
                    "text": "Third variant",
                    "char_count": 13,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
            ]
        }
    )
    parsed = caption_template.parse_caption_generation_response(raw, make_context())
    assert parsed.was_repaired is True
    assert parsed.data.variants[0].char_count == len(parsed.data.variants[0].text)


def test_parse_wrong_variant_count_raises() -> None:
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "Only one",
                    "char_count": 8,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                }
            ]
        }
    )
    with pytest.raises(ValueError):
        caption_template.parse_caption_generation_response(raw, make_context())


def test_parse_missing_platform_variants_raises() -> None:
    context = make_context().model_copy(
        update={
            "target_platforms": [Platform.instagram, Platform.linkedin],
            "platform_constraints": [
                {
                    "platform": Platform.instagram,
                    "max_chars": 2200,
                    "supports_hashtags": True,
                    "supports_links": False,
                    "supports_emojis": True,
                },
                {
                    "platform": Platform.linkedin,
                    "max_chars": 3000,
                    "supports_hashtags": True,
                    "supports_links": True,
                    "supports_emojis": True,
                },
            ],
        }
    )
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "Caption A",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v2",
                    "text": "Caption B",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v3",
                    "text": "Caption C",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v1",
                    "text": "Caption D",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v2",
                    "text": "Caption E",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "instagram",
                    "variant_id": "v3",
                    "text": "Caption F",
                    "char_count": 9,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
            ]
        }
    )
    with pytest.raises(ValueError):
        caption_template.parse_caption_generation_response(raw, context)


def test_parse_char_limit_exceeded_raises() -> None:
    context = make_context().model_copy(
        update={
            "target_platforms": [Platform.x],
            "platform_constraints": [
                {
                    "platform": Platform.x,
                    "max_chars": 280,
                    "supports_hashtags": True,
                    "supports_links": True,
                    "supports_emojis": True,
                }
            ],
        }
    )
    too_long = "x" * 281
    raw = json.dumps(
        {
            "variants": [
                {
                    "platform": "x",
                    "variant_id": "v1",
                    "text": too_long,
                    "char_count": 281,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "x",
                    "variant_id": "v2",
                    "text": "ok",
                    "char_count": 2,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
                {
                    "platform": "x",
                    "variant_id": "v3",
                    "text": "ok2",
                    "char_count": 3,
                    "contains_cta": True,
                    "included_keywords": ["social automation"],
                },
            ]
        }
    )
    with pytest.raises(ValueError):
        caption_template.parse_caption_generation_response(raw, context)


def test_platform_constraints_missing_for_platform_raises() -> None:
    with pytest.raises(ValueError):
        CaptionContext(
            company_id=uuid4(),
            company_name="Acme",
            company_positioning="AI-first social media automation",
            tone_fingerprint={"formality": 0.7},
            post_intent=PostIntent.promote,
            core_message="Launch your campaign faster with intelligent optimization.",
            cta_requirements=["learn_more"],
            audience_profile={"segment": "marketers"},
            seo_keywords=["social automation"],
            target_platforms=[Platform.instagram],
            platform_constraints=[],
        )
