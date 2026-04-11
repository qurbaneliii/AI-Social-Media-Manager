# FILE: packages/prompt-templates/tests/test_context_models.py
from __future__ import annotations

from uuid import uuid4

import pytest

from packages.prompt_templates.context_models.audience_context import AudienceContext
from packages.prompt_templates.context_models.caption_context import CaptionContext
from packages.prompt_templates.context_models.hashtag_context import HashtagContext
from packages.types.enums import Platform, PostIntent


def test_audience_context_invalid_json_raises() -> None:
    with pytest.raises(ValueError):
        AudienceContext(
            company_id=uuid4(),
            platforms=[Platform.linkedin],
            company_profile_json="{bad-json",
            post_intent=PostIntent.educate,
            content_topic="Topic",
            value_prop="Strong value proposition",
        )


def test_caption_context_empty_tone_fingerprint_raises() -> None:
    with pytest.raises(ValueError):
        CaptionContext(
            company_id=uuid4(),
            company_name="Acme",
            company_positioning="AI-first social media automation",
            tone_fingerprint={},
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


def test_caption_context_empty_audience_profile_raises() -> None:
    with pytest.raises(ValueError):
        CaptionContext(
            company_id=uuid4(),
            company_name="Acme",
            company_positioning="AI-first social media automation",
            tone_fingerprint={"formality": 0.6},
            post_intent=PostIntent.promote,
            core_message="Launch your campaign faster with intelligent optimization.",
            cta_requirements=["learn_more"],
            audience_profile={},
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


def test_caption_context_missing_platform_constraints_raises() -> None:
    with pytest.raises(ValueError):
        CaptionContext(
            company_id=uuid4(),
            company_name="Acme",
            company_positioning="AI-first social media automation",
            tone_fingerprint={"formality": 0.6},
            post_intent=PostIntent.promote,
            core_message="Launch your campaign faster with intelligent optimization.",
            cta_requirements=["learn_more"],
            audience_profile={"segment": "marketers"},
            seo_keywords=["social automation"],
            target_platforms=[Platform.instagram],
            platform_constraints=[
                {
                    "platform": Platform.linkedin,
                    "max_chars": 3000,
                    "supports_hashtags": True,
                    "supports_links": True,
                    "supports_emojis": True,
                }
            ],
        )


def test_hashtag_context_invalid_tags_raises() -> None:
    with pytest.raises(ValueError):
        HashtagContext(
            company_id=uuid4(),
            platform=Platform.instagram,
            post_topic="Practical social campaign automation tips",
            industry_vertical="MarTech",
            audience_summary="Growth teams in SMB SaaS",
            brand_positioning="Reliable AI support for marketers",
            historical_tags=["bad_tag"],
            banned_tags=[],
        )

    with pytest.raises(ValueError):
        HashtagContext(
            company_id=uuid4(),
            platform=Platform.instagram,
            post_topic="Practical social campaign automation tips",
            industry_vertical="MarTech",
            audience_summary="Growth teams in SMB SaaS",
            brand_positioning="Reliable AI support for marketers",
            historical_tags=["#bad tag"],
            banned_tags=[],
        )

    with pytest.raises(ValueError):
        HashtagContext(
            company_id=uuid4(),
            platform=Platform.instagram,
            post_topic="Practical social campaign automation tips",
            industry_vertical="MarTech",
            audience_summary="Growth teams in SMB SaaS",
            brand_positioning="Reliable AI support for marketers",
            historical_tags=["#ok"],
            banned_tags=["bad"],
        )
