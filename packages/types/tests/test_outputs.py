from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.types.enums import ApprovalMode, Platform, ReadingLevel, ReasonCode, RiskFlag, ScheduleStatus
from packages.types.outputs import (
    AgeRange,
    AudienceOutput,
    AudienceProfile,
    CaptionGenerationOutput,
    CaptionVariant,
    HashtagOutput,
    PostGenerationOutput,
    QualityOutput,
    RankedHashtag,
    RankedWindow,
    ScheduleOutput,
    ScheduledTarget,
    SeoMetadata,
    SeoOutput,
)


def valid_caption_variant(platform: Platform) -> CaptionVariant:
    return CaptionVariant(
        platform=platform,
        caption_text="A concise and engaging caption for growth-focused audiences.",
        hashtags=["#growth"],
        policy_compliance_score=0.9,
        engagement_predicted=0.8,
        tone_match=0.85,
        cta_present=True,
        keyword_inclusion=0.75,
        platform_compliance=0.95,
        final_score=0.88,
    )


def test_caption_output_rejects_duplicate_variant_platforms() -> None:
    v1 = valid_caption_variant(Platform.linkedin)
    v2 = valid_caption_variant(Platform.linkedin)
    with pytest.raises(ValidationError):
        CaptionGenerationOutput(
            company_id=uuid4(),
            variants=[v1, v2],
            selected_variants_by_platform={"linkedin": v1},
            confidence_score=0.9,
            generated_at=datetime.now(UTC),
        )


def test_hashtag_output_rejects_duplicate_hashtags() -> None:
    with pytest.raises(ValidationError):
        HashtagOutput(
            company_id=uuid4(),
            hashtags=[
                RankedHashtag(hashtag="#ai", score=0.9, tier="niche"),
                RankedHashtag(hashtag="#AI", score=0.8, tier="broad"),
            ],
            confidence_score=0.8,
            generated_at=datetime.now(UTC),
        )


def test_age_range_rejects_invalid_bounds() -> None:
    with pytest.raises(ValidationError):
        AgeRange(min_age=45, max_age=30)


def test_schedule_output_rejects_target_platform_without_window() -> None:
    with pytest.raises(ValidationError):
        ScheduleOutput(
            post_id=uuid4(),
            company_id=uuid4(),
            windows=[
                RankedWindow(
                    platform=Platform.linkedin,
                    dow=2,
                    hour=10,
                    score=0.7,
                    confidence=0.8,
                    reason_codes=[ReasonCode.historical_win],
                )
            ],
            targets=[
                ScheduledTarget(
                    platform=Platform.instagram,
                    run_at_utc=datetime.now(UTC),
                    status=ScheduleStatus.queued,
                )
            ],
            approval_mode=ApprovalMode.auto,
            generated_at=datetime.now(UTC),
        )


def test_quality_output_rejects_duplicate_risk_flags() -> None:
    with pytest.raises(ValidationError):
        QualityOutput(
            company_id=uuid4(),
            post_id=uuid4(),
            overall_score=0.75,
            policy_compliance_score=0.88,
            reading_level=ReadingLevel.professional,
            risk_flags=[RiskFlag.jargon_heavy, RiskFlag.jargon_heavy],
            generated_at=datetime.now(UTC),
        )


def test_post_generation_output_happy_path() -> None:
    caption = CaptionGenerationOutput(
        company_id=uuid4(),
        variants=[valid_caption_variant(Platform.linkedin)],
        selected_variants_by_platform={"linkedin": valid_caption_variant(Platform.linkedin)},
        confidence_score=0.9,
        generated_at=datetime.now(UTC),
    )
    hashtags = HashtagOutput(
        company_id=uuid4(),
        hashtags=[RankedHashtag(hashtag="#ai", score=0.9, tier="niche")],
        confidence_score=0.8,
        generated_at=datetime.now(UTC),
    )
    audience = AudienceOutput(
        company_id=uuid4(),
        profile=AudienceProfile(
            age_range=AgeRange(min_age=25, max_age=45),
            segments=["product leaders"],
            psychographics={"innovation": 0.7},
            platform_segments={Platform.linkedin: ["B2B SaaS"]},
        ),
        confidence_score=0.84,
        generated_at=datetime.now(UTC),
    )
    schedule = ScheduleOutput(
        post_id=uuid4(),
        company_id=uuid4(),
        windows=[
            RankedWindow(
                platform=Platform.linkedin,
                dow=2,
                hour=10,
                score=0.7,
                confidence=0.8,
                reason_codes=[ReasonCode.historical_win],
            )
        ],
        targets=[
            ScheduledTarget(
                platform=Platform.linkedin,
                run_at_utc=datetime.now(UTC),
                status=ScheduleStatus.queued,
            )
        ],
        approval_mode=ApprovalMode.auto,
        generated_at=datetime.now(UTC),
    )
    seo = SeoOutput(
        company_id=uuid4(),
        seo_metadata=SeoMetadata(
            meta_title="High Impact Social Strategy",
            meta_description="A concise SEO description for social campaign publication.",
            alt_text="A marketing team planning a social launch.",
        ),
        confidence_score=0.82,
        generated_at=datetime.now(UTC),
    )
    quality = QualityOutput(
        company_id=uuid4(),
        post_id=uuid4(),
        overall_score=0.78,
        policy_compliance_score=0.92,
        reading_level=ReadingLevel.professional,
        risk_flags=[RiskFlag.jargon_heavy],
        generated_at=datetime.now(UTC),
    )

    model = PostGenerationOutput(
        post_id=uuid4(),
        company_id=uuid4(),
        status="generated",
        caption=caption,
        hashtags=hashtags,
        audience=audience,
        schedule=schedule,
        seo=seo,
        quality=quality,
        generated_at=datetime.now(UTC),
    )

    assert model.status == "generated"
