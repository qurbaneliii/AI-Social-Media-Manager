from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.types.enums import CTAType, MarketSegment, Platform, PostArchiveFormat, PostIntent, UrgencyLevel
from packages.types.inputs import CompanyOnboardingProfile, PerformanceFeedback, PerformanceFeedbackBatch, PostGenerationRequest


def valid_onboarding_payload() -> dict:
    return {
        "company_name": "Acme Labs",
        "industry_vertical": "AI Software",
        "target_market": {
            "regions": ["US", "DE"],
            "segments": [MarketSegment.B2B],
            "persona_summary": "Decision makers in growth-stage software organizations.",
        },
        "brand_positioning_statement": "We help small teams launch high-performing campaigns with trustworthy automation.",
        "tone_of_voice_descriptors": ["clear", "confident", "helpful"],
        "competitor_list": ["CompetitorOne"],
        "platform_presence": {
            "instagram": True,
            "linkedin": True,
            "facebook": False,
            "x": False,
            "tiktok": False,
            "pinterest": False,
        },
        "posting_frequency_goal": {
            "instagram": 3,
            "linkedin": 2,
            "facebook": 0,
            "x": 0,
            "tiktok": 0,
            "pinterest": 0,
        },
        "primary_cta_types": [CTAType.learn_more],
        "brand_color_hex_codes": ["#112233", "#AABBCC"],
        "approved_vocabulary_list": ["analytics"],
        "banned_vocabulary_list": ["guarantee"],
        "previous_post_archive": {
            "format": PostArchiveFormat.csv,
            "s3_uri": "s3://acme-bucket/archives/posts.csv",
        },
        "brand_guidelines_pdf": "s3://acme-bucket/guidelines/brand.pdf",
        "logo_file": str(uuid4()),
        "sample_post_images": [str(uuid4())],
    }


def test_company_onboarding_rejects_invalid_region() -> None:
    payload = valid_onboarding_payload()
    payload["target_market"]["regions"] = ["US", "XX"]
    with pytest.raises(ValidationError):
        CompanyOnboardingProfile(**payload)


def test_company_onboarding_rejects_frequency_on_disabled_platform() -> None:
    payload = valid_onboarding_payload()
    payload["posting_frequency_goal"]["facebook"] = 2
    with pytest.raises(ValidationError):
        CompanyOnboardingProfile(**payload)


def test_company_onboarding_rejects_vocab_overlap() -> None:
    payload = valid_onboarding_payload()
    payload["banned_vocabulary_list"] = ["analytics"]
    with pytest.raises(ValidationError):
        CompanyOnboardingProfile(**payload)


def test_post_request_rejects_duplicate_platforms() -> None:
    with pytest.raises(ValidationError):
        PostGenerationRequest(
            company_id=uuid4(),
            post_intent=PostIntent.announce,
            core_message="This post explains our newest product launch in detail for enterprise teams.",
            target_platforms=[Platform.linkedin, Platform.linkedin],
            urgency_level=UrgencyLevel.immediate,
        )


def test_post_request_rejects_scheduled_without_future_datetime() -> None:
    with pytest.raises(ValidationError):
        PostGenerationRequest(
            company_id=uuid4(),
            post_intent=PostIntent.promote,
            core_message="A detailed promo post designed for product adoption and measurable engagement.",
            target_platforms=[Platform.instagram],
            urgency_level=UrgencyLevel.scheduled,
            requested_publish_at=datetime.now(UTC) + timedelta(minutes=2),
        )


def test_feedback_batch_rejects_duplicate_post_platform_pair() -> None:
    post_id = uuid4()
    record = PerformanceFeedback(
        post_id=post_id,
        platform=Platform.linkedin,
        external_post_id="ln_1",
        impressions=1000,
        reach=900,
        engagement_rate=0.12,
        click_through_rate=0.03,
        saves=10,
        shares=4,
        follower_growth_delta=5,
        posting_timestamp=datetime.now(UTC) - timedelta(hours=2),
        captured_at=datetime.now(UTC),
    )
    with pytest.raises(ValidationError):
        PerformanceFeedbackBatch(records=[record, record])
