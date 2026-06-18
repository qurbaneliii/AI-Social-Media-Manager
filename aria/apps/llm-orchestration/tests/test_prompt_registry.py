from __future__ import annotations

from ai.prompts import PromptRegistry
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


def test_prompt_registry_loads_versioned_prompts() -> None:
    registry = PromptRegistry()

    assert registry.get("brand_system").version == "v1"
    assert "Instagram" in registry.get("platform_adaptation").content
    for prompt_key in [
        "brand_strategy",
        "competitor_analysis",
        "trend_research",
        "hashtag_recommendation",
        "visual_concept",
        "calendar_planning",
        "community_management",
        "reporting_insight",
    ]:
        assert registry.get(prompt_key).version == "v1"


def test_prompt_registry_builds_content_messages() -> None:
    registry = PromptRegistry()
    request = ContentRequest(
        brand_profile=make_brand(),
        platform_context=PlatformContext(platform="linkedin", content_type="post", objective="educate"),
        campaign_objective="build trust",
        topic="AI content approval",
        content_pillar="authority",
    )

    messages = registry.build_content_generation_messages(request)

    assert [message.role for message in messages] == ["system", "system", "user"]
    assert "AI content approval" in messages[-1].content


def test_prompt_registry_builds_specialist_agent_messages() -> None:
    registry = PromptRegistry()

    messages = registry.build_agent_messages("trend_research", {"topic": "AI marketing"})

    assert [message.role for message in messages] == ["system", "system", "user"]
    assert "AI marketing" in messages[-1].content
