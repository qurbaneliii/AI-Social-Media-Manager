from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from ai.schemas.analytics import ReportingInsightRequest
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest, ContentCalendarPlan
from ai.schemas.community import CommunityManagementRequest, CommunityMessageAnalysis
from ai.schemas.competitor import CompetitorAnalysisRequest, CompetitorPostData
from ai.schemas.content import ContentRequest, GeneratedContentPackage, PlatformContext
from ai.schemas.evaluation import AIQualityReview
from ai.schemas.hashtag import HashtagRecommendation
from ai.schemas.strategy import BrandStrategyPlan, BrandStrategyRequest
from ai.schemas.trend import TrendInputData, TrendResearchRequest
from ai.schemas.visual import VisualConceptRequest


def make_brand() -> BrandProfile:
    return BrandProfile(
        brand_id="brand-1",
        brand_name="ARIA Labs",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
    )


def test_content_request_schema_accepts_required_brand_context() -> None:
    request = ContentRequest(
        brand_profile=make_brand(),
        platform_context=PlatformContext(platform="linkedin", content_type="post", objective="educate"),
        campaign_objective="build trust",
        topic="approval-based AI content",
        content_pillar="authority",
    )

    assert request.brand_profile.brand_name == "ARIA Labs"
    assert request.number_of_variants == 1


def test_quality_scores_are_bounded() -> None:
    with pytest.raises(ValidationError):
        AIQualityReview(
            brand_consistency_score=1.2,
            platform_fit_score=0.8,
            clarity_score=0.8,
            cta_strength_score=0.8,
            originality_score=0.8,
            factual_risk_score=0.1,
            safety_risk_score=0.1,
            engagement_potential_score=0.8,
            approval_status="approved",
        )


def test_generated_package_normalizes_hashtags() -> None:
    package = GeneratedContentPackage(
        platform="instagram",
        content_type="caption",
        hook="Hook",
        caption="Caption",
        cta="Approve draft",
        hashtags=["socialmedia"],
        rationale="Test",
    )

    assert package.hashtags == ["#socialmedia"]


def test_phase_2_request_schemas_accept_structured_inputs() -> None:
    brand = make_brand()

    assert BrandStrategyRequest(brand_profile=brand, business_goal="grow trust", platforms=["linkedin"])
    assert CompetitorAnalysisRequest(
        brand_profile=brand,
        competitors=[CompetitorPostData(competitor_name="Other", platform="linkedin", content_type="post")],
    )
    assert TrendResearchRequest(
        brand_profile=brand,
        trends=[TrendInputData(keyword="AI approval")],
    )
    assert VisualConceptRequest(
        brand_profile=brand,
        platform_context=PlatformContext(platform="instagram", content_type="carousel", objective="educate"),
        topic="AI approvals",
        content_pillar="education",
        campaign_objective="trust",
    )
    assert CalendarPlanningRequest(
        brand_profile=brand,
        start_date=date(2026, 6, 20),
        end_date=date(2026, 6, 26),
    )
    assert CommunityManagementRequest(brand_profile=brand, platform="instagram", message_text="What is the price?")
    assert ReportingInsightRequest(brand_profile=brand, reporting_period="June", analytics_data={"views": 10})


def test_phase_2_output_schemas_enforce_approval_based_defaults() -> None:
    strategy = BrandStrategyPlan(positioning_statement="Position")
    calendar = ContentCalendarPlan(items=[], rationale="Draft")
    community = CommunityMessageAnalysis(
        message_text="Help",
        sentiment="neutral",
        intent="question",
        urgency="normal",
        toxicity_risk=0,
        crisis_risk=0,
        suggested_reply="Thanks, a human will review this.",
        confidence=0.8,
    )
    hashtags = HashtagRecommendation(niche_hashtags=["AI"], rationale="Grouped recommendations")

    assert strategy.approval_required is True
    assert calendar.approval_required is True
    assert community.requires_human_review is True
    assert community.auto_reply_allowed is False
    assert hashtags.niche_hashtags == ["#AI"]
