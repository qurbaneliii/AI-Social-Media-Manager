from __future__ import annotations

import asyncio

from ai.agents import AIOrchestrator
from ai.llm import LLMClient, LLMSettings
from ai.llm.types import LLMMetadata
from ai.schemas.brand import BrandProfile
from ai.schemas.content import ContentRequest, PlatformContext


def make_brand() -> BrandProfile:
    return BrandProfile(
        brand_id="brand-1",
        brand_name="ARIA Labs",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
    )


def test_orchestrator_generates_content_package_in_mock_mode() -> None:
    asyncio.run(_run_orchestrator_mock_mode())


async def _run_orchestrator_mock_mode() -> None:
    orchestrator = AIOrchestrator(
        llm_client=LLMClient(
            LLMSettings(
                OPENAI_API_KEY=None,
                AI_MOCK_MODE=True,
                OPENAI_MODEL="gpt-4o-mini",
                AI_TEMPERATURE=0.4,
            )
        )
    )
    request = ContentRequest(
        brand_profile=make_brand(),
        platform_context=PlatformContext(
            platform="linkedin",
            content_type="post",
            objective="educate",
            hashtag_limit=3,
        ),
        campaign_objective="build trust",
        topic="AI content approval",
        content_pillar="authority",
    )

    package = await orchestrator.generate_content_package(request)

    assert package.platform == "linkedin"
    assert package.quality_scores is not None
    assert package.quality_scores.approval_status == "requires_human_review"
    assert len(package.hashtags) <= 3


def test_llm_client_emits_metadata_in_mock_mode() -> None:
    asyncio.run(_run_orchestrator_with_metadata_hook())


async def _run_orchestrator_with_metadata_hook() -> None:
    events: list[LLMMetadata] = []
    orchestrator = AIOrchestrator(
        llm_client=LLMClient(
            LLMSettings(
                OPENAI_API_KEY=None,
                AI_MOCK_MODE=True,
                OPENAI_MODEL="gpt-4o-mini",
                AI_TEMPERATURE=0.4,
            ),
            metadata_hook=events.append,
        )
    )
    request = ContentRequest(
        brand_profile=make_brand(),
        platform_context=PlatformContext(platform="linkedin", content_type="post", objective="educate"),
        campaign_objective="build trust",
        topic="AI content approval",
        content_pillar="authority",
    )

    await orchestrator.generate_content_package(request)

    assert [event.mock_mode for event in events] == [True, True]
    assert {event.extra["schema"] for event in events} == {"GeneratedContentPackage", "AIQualityReview"}
    assert all(event.extra["estimated_cost_usd"] == 0.0 for event in events)
