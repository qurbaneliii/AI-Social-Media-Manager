from __future__ import annotations

import asyncio
from datetime import date

from ai.agents import (
    BrandStrategyAgent,
    CalendarPlanningAgent,
    CommunityManagementAgent,
    CompetitorAnalysisAgent,
    HashtagAgent,
    ReportingAgent,
    TrendResearchAgent,
    VisualConceptAgent,
)
from ai.llm import LLMClient, LLMSettings
from ai.prompts import PromptRegistry
from ai.schemas.analytics import ReportingInsightRequest
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest
from ai.schemas.community import CommunityManagementRequest
from ai.schemas.competitor import CompetitorAnalysisRequest, CompetitorPostData
from ai.schemas.content import PlatformContext
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
        platforms=["linkedin", "instagram"],
    )


def make_client() -> LLMClient:
    return LLMClient(
        LLMSettings(
            OPENAI_API_KEY=None,
            AI_MOCK_MODE=True,
            OPENAI_MODEL="gpt-4o-mini",
            AI_TEMPERATURE=0.4,
        )
    )


def test_phase_2_agents_run_in_mock_mode() -> None:
    asyncio.run(_run_phase_2_agents())


async def _run_phase_2_agents() -> None:
    brand = make_brand()
    registry = PromptRegistry()
    client = make_client()
    platform = PlatformContext(platform="linkedin", content_type="post", objective="educate", hashtag_limit=5)

    strategy = await BrandStrategyAgent(client, registry).create_strategy(
        BrandStrategyRequest(brand_profile=brand, business_goal="build trust", platforms=["linkedin"])
    )
    competitors = await CompetitorAnalysisAgent(client, registry).analyze(
        CompetitorAnalysisRequest(
            brand_profile=brand,
            competitors=[
                CompetitorPostData(
                    competitor_name="Other",
                    platform="linkedin",
                    content_type="carousel",
                    hashtags=["#AI"],
                )
            ],
        )
    )
    trends = await TrendResearchAgent(client, registry).research(
        TrendResearchRequest(brand_profile=brand, trends=[TrendInputData(keyword="AI approval")])
    )
    hashtags = await HashtagAgent(client, registry).recommend(
        HashtagRecommendationRequest(brand_profile=brand, platform_context=platform, topic="AI approval")
    )
    visual = await VisualConceptAgent(client, registry).generate(
        VisualConceptRequest(
            brand_profile=brand,
            platform_context=platform,
            topic="AI approval",
            content_pillar="education",
            campaign_objective="trust",
        )
    )
    calendar = await CalendarPlanningAgent(client, registry).create_calendar(
        CalendarPlanningRequest(
            brand_profile=brand,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 26),
            platforms=["linkedin"],
        )
    )
    community = await CommunityManagementAgent(client, registry).analyze(
        CommunityManagementRequest(brand_profile=brand, platform="instagram", message_text="I need a refund urgently")
    )
    report = await ReportingAgent(client, registry).generate_insights(
        ReportingInsightRequest(brand_profile=brand, reporting_period="June", analytics_data={"views": 100})
    )

    assert strategy.approval_required is True
    assert competitors.source_limitations
    assert trends.source_limitations
    assert hashtags.niche_hashtags[0].startswith("#")
    assert visual.image_generation_prompts
    assert calendar.items and all(item.approval_required for item in calendar.items)
    assert community.requires_human_review is True
    assert community.auto_reply_allowed is False
    assert report.next_experiments
