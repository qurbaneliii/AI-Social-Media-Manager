# FILE: packages/prompt-templates/tests/test_validators.py
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from packages.prompt_templates.base import PromptValidationError
from packages.prompt_templates.context_models.audience_context import AudienceContext
from packages.prompt_templates.context_models.caption_context import CaptionContext
from packages.prompt_templates.context_models.hashtag_context import HashtagContext
from packages.prompt_templates.context_models.seo_context import SEOContext
from packages.prompt_templates.context_models.tone_context import ToneContext
from packages.prompt_templates.templates.caption import build_caption_generation_prompt
from packages.prompt_templates.templates.hashtag import build_hashtag_generation_prompt
from packages.prompt_templates.templates.seo import build_seo_optimization_prompt
from packages.prompt_templates.templates.tone_calibration import build_tone_calibration_prompt
from packages.prompt_templates.validators import (
    validate_audience_prompt,
    validate_caption_prompt,
    validate_hashtag_prompt,
    validate_seo_prompt,
    validate_tone_calibration_prompt,
)
from packages.types.enums import MarketSegment, Platform, PostIntent


def caption_context() -> CaptionContext:
    return CaptionContext(
        company_id=uuid4(),
        company_name="Acme",
        company_positioning="AI-first social media automation",
        tone_fingerprint={"formality": 0.7},
        approved_vocabulary_list=["automation"],
        banned_vocabulary_list=["forbidden"],
        post_intent=PostIntent.promote,
        core_message="Launch your campaign faster with intelligent optimization.",
        cta_requirements=["learn_more"],
        audience_profile={"segment": "marketers"},
        seo_keywords=["social automation"],
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


def seo_context() -> SEOContext:
    return SEOContext(
        company_id=uuid4(),
        post_caption="Antidisestablishmentarianism institutionalization epistemological operationalization.",
        industry_vertical="MarTech",
        target_keywords=["marketing automation"],
        platform=Platform.linkedin,
        market_segment=MarketSegment.B2B,
    )


def tone_context_valid() -> ToneContext:
    return ToneContext(
        company_id=uuid4(),
        company_name="Acme",
        tone_descriptors=["clear", "practical", "optimistic"],
        brand_positioning="We help lean marketing teams execute social strategy with confidence and consistency.",
        sample_posts=[
            {"text": "A sufficiently long sample post for validation checks.", "platform": Platform.linkedin},
            {"text": "Another sufficiently long sample post for validation checks.", "platform": Platform.linkedin},
            {"text": "Third sufficiently long sample post for validation checks.", "platform": Platform.facebook},
            {"text": "Fourth sufficiently long sample post for validation checks.", "platform": Platform.x},
            {"text": "Fifth sufficiently long sample post for validation checks.", "platform": Platform.instagram},
        ],
        banned_vocabulary=[],
    )


def test_validate_caption_missing_banned_list_fails() -> None:
    ctx = caption_context().model_copy(update={"banned_vocabulary_list": []})
    messages = build_caption_generation_prompt(ctx)
    with pytest.raises(PromptValidationError):
        validate_caption_prompt(messages, ctx)


def test_validate_caption_token_budget_exceeded_fails() -> None:
    ctx = caption_context()
    messages = build_caption_generation_prompt(ctx)
    messages[1]["content"] = messages[1]["content"] + " superlong" * 10000
    with pytest.raises(PromptValidationError):
        validate_caption_prompt(messages, ctx)


def test_validate_caption_success_true() -> None:
    ctx = caption_context()
    messages = build_caption_generation_prompt(ctx)
    assert validate_caption_prompt(messages, ctx) is True


def test_validate_caption_unresolved_placeholder_fails() -> None:
    ctx = caption_context()
    messages = build_caption_generation_prompt(ctx)
    messages[1]["content"] += " {{UNRESOLVED}}"
    with pytest.raises(PromptValidationError):
        validate_caption_prompt(messages, ctx)


def test_validate_seo_b2b_low_flesch_is_warning_not_error(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = seo_context()
    messages = build_seo_optimization_prompt(ctx)
    monkeypatch.setattr("packages.prompt_templates.validators.textstat.flesch_reading_ease", lambda _: 10.0)
    assert validate_seo_prompt(messages, ctx) is True


def test_validate_seo_banned_term_fails() -> None:
    ctx = seo_context().model_copy(update={"banned_vocabulary": ["operationalization"]})
    messages = build_seo_optimization_prompt(ctx)
    with pytest.raises(PromptValidationError):
        validate_seo_prompt(messages, ctx)


def test_validate_hashtag_invalid_platform_fails() -> None:
    ctx = HashtagContext.model_construct(
        company_id=uuid4(),
        platform="not-a-platform",
        post_topic="Topic for validation checks",
        industry_vertical="MarTech",
        audience_summary="Audience summary text",
        brand_positioning="Positioning text long enough",
        trending_context=[],
        historical_tags=[],
        banned_tags=[],
    )
    messages = build_hashtag_generation_prompt(
        HashtagContext(
            company_id=uuid4(),
            platform=Platform.instagram,
            post_topic="Topic for validation checks",
            industry_vertical="MarTech",
            audience_summary="Audience summary text",
            brand_positioning="Positioning text long enough",
        )
    )
    with pytest.raises(PromptValidationError):
        validate_hashtag_prompt(messages, ctx)


def test_validate_hashtag_empty_topic_fails() -> None:
    ctx = HashtagContext.model_construct(
        company_id=uuid4(),
        platform=Platform.instagram,
        post_topic="   ",
        industry_vertical="MarTech",
        audience_summary="Audience summary text",
        brand_positioning="Positioning text long enough",
        trending_context=[],
        historical_tags=[],
        banned_tags=[],
    )
    messages = build_hashtag_generation_prompt(
        HashtagContext(
            company_id=uuid4(),
            platform=Platform.instagram,
            post_topic="Topic for validation checks",
            industry_vertical="MarTech",
            audience_summary="Audience summary text",
            brand_positioning="Positioning text long enough",
        )
    )
    with pytest.raises(PromptValidationError):
        validate_hashtag_prompt(messages, ctx)


def test_validate_audience_invalid_json_fails() -> None:
    ctx = AudienceContext.model_construct(
        company_id=uuid4(),
        platforms=[Platform.linkedin],
        company_profile_json="{bad-json",
        post_intent=PostIntent.educate,
        content_topic="Audience topic",
        value_prop="Strong value proposition",
        top_segments=[],
        weak_segments=[],
        historical_notes="",
        market_segment=MarketSegment.B2C,
    )
    messages = [{"role": "system", "content": "ok"}, {"role": "user", "content": "ok"}]
    with pytest.raises(PromptValidationError):
        validate_audience_prompt(messages, ctx)


def test_validate_audience_invalid_post_intent_fails() -> None:
    ctx = AudienceContext.model_construct(
        company_id=uuid4(),
        platforms=[Platform.linkedin],
        company_profile_json=json.dumps({"ok": True}),
        post_intent="bad-intent",
        content_topic="Audience topic",
        value_prop="Strong value proposition",
        top_segments=[],
        weak_segments=[],
        historical_notes="",
        market_segment=MarketSegment.B2C,
    )
    messages = [{"role": "system", "content": "ok"}, {"role": "user", "content": "ok"}]
    with pytest.raises(PromptValidationError):
        validate_audience_prompt(messages, ctx)


def test_validate_tone_insufficient_samples_fails() -> None:
    valid = tone_context_valid()
    ctx = valid.model_copy(update={"sample_posts": valid.sample_posts[:4]})
    messages = build_tone_calibration_prompt(valid)
    with pytest.raises(PromptValidationError):
        validate_tone_calibration_prompt(messages, ctx)


def test_validate_tone_unresolved_placeholder_fails() -> None:
    ctx = tone_context_valid()
    messages = build_tone_calibration_prompt(ctx)
    messages[1]["content"] += " {{UNRESOLVED}}"
    with pytest.raises(PromptValidationError):
        validate_tone_calibration_prompt(messages, ctx)
