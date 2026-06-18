from __future__ import annotations

import asyncio
from datetime import date

from ai.agents import AIOrchestrator
from ai.llm import LLMClient, LLMSettings
from ai.schemas.analytics import ReportingInsightRequest
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest
from ai.schemas.community import CommunityManagementRequest
from ai.schemas.competitor import CompetitorAnalysisRequest
from ai.schemas.content import ContentRequest, GeneratedContentPackage, PlatformContext
from ai.schemas.hashtag import HashtagRecommendationRequest
from ai.schemas.strategy import BrandStrategyRequest
from ai.schemas.trend import TrendInputData, TrendResearchRequest
from ai.schemas.visual import VisualConceptRequest


def make_brand() -> BrandProfile:
    return BrandProfile(
        brand_id="brand-1",
        brand_name="ARIA Labs",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
        platforms=["linkedin"],
    )


def make_orchestrator() -> AIOrchestrator:
    return AIOrchestrator(
        llm_client=LLMClient(
            LLMSettings(
                OPENAI_API_KEY=None,
                AI_MOCK_MODE=True,
                OPENAI_MODEL="gpt-4o-mini",
                AI_TEMPERATURE=0.4,
            )
        )
    )


def test_orchestrator_routes_phase_2_specialist_agents() -> None:
    asyncio.run(_run_orchestrator_routes())


async def _run_orchestrator_routes() -> None:
    brand = make_brand()
    orchestrator = make_orchestrator()
    platform = PlatformContext(platform="linkedin", content_type="post", objective="educate")

    strategy = await orchestrator.create_brand_strategy(
        BrandStrategyRequest(brand_profile=brand, business_goal="build trust")
    )
    competitors = await orchestrator.analyze_competitors(CompetitorAnalysisRequest(brand_profile=brand))
    trends = await orchestrator.research_trends(
        TrendResearchRequest(brand_profile=brand, trends=[TrendInputData(keyword="AI approvals")])
    )
    hashtags = await orchestrator.recommend_hashtags(
        HashtagRecommendationRequest(brand_profile=brand, platform_context=platform, topic="AI approval")
    )
    visual = await orchestrator.generate_visual_concept(
        VisualConceptRequest(
            brand_profile=brand,
            platform_context=platform,
            topic="AI approval",
            content_pillar="education",
            campaign_objective="trust",
        )
    )
    calendar = await orchestrator.create_content_calendar(
        CalendarPlanningRequest(brand_profile=brand, start_date=date(2026, 6, 20), end_date=date(2026, 6, 26))
    )
    community = await orchestrator.analyze_community_message(
        CommunityManagementRequest(brand_profile=brand, platform="linkedin", message_text="Is there a demo?")
    )
    report = await orchestrator.generate_report_insights(
        ReportingInsightRequest(brand_profile=brand, reporting_period="June", analytics_data={"clicks": 4})
    )
    review = await orchestrator.review_content_quality(
        ContentRequest(
            brand_profile=brand,
            platform_context=platform,
            campaign_objective="trust",
            topic="AI approval",
            content_pillar="education",
        ),
        GeneratedContentPackage(
            platform="linkedin",
            content_type="post",
            hook="Hook",
            caption="Caption",
            cta="Approve",
            rationale="Test",
            risks=["Needs review"],
        ),
    )

    assert strategy.positioning_statement
    assert competitors.source_limitations
    assert trends.relevant_topics
    assert hashtags.rationale
    assert visual.visual_brief
    assert calendar.items
    assert community.auto_reply_allowed is False
    assert report.summary
    assert review.approval_status == "requires_human_review"
