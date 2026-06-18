from __future__ import annotations

from ai.schemas.strategy import BrandStrategyPlan, BrandStrategyRequest

from .base import BaseAgent


class BrandStrategyAgent(BaseAgent):
    async def create_strategy(self, request: BrandStrategyRequest) -> BrandStrategyPlan:
        messages = self.prompt_registry.build_agent_messages(
            "brand_strategy",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            BrandStrategyPlan,
            mock_factory=lambda: self._mock_strategy(request),
        )

    def _mock_strategy(self, request: BrandStrategyRequest) -> dict:
        brand = request.brand_profile
        platforms = request.platforms or brand.platforms or ["linkedin"]
        pillars = brand.business_goals[:2] + ["education", "proof", "community"]
        return {
            "positioning_statement": (
                f"{brand.brand_name} helps {', '.join(brand.target_audience) or 'its audience'} "
                f"make progress on {request.business_goal} with a {brand.industry} point of view."
            ),
            "audience_hypotheses": [
                f"{brand.target_audience[0]} need practical examples before they trust AI-assisted workflows."
                if brand.target_audience
                else "The target audience needs clear proof before considering a new brand workflow."
            ],
            "content_pillars": list(dict.fromkeys(pillars))[:5],
            "campaign_angles": [
                f"Show the cost of delaying {request.business_goal}.",
                "Turn brand expertise into short educational series.",
            ],
            "platform_recommendations": {
                platform: ["Use native format conventions.", "Keep every draft approval-based."] for platform in platforms
            },
            "strategic_recommendations": [
                "Validate positioning with human stakeholders before launching campaigns.",
                "Create reusable pillar definitions before scaling generation.",
            ],
            "risks": ["Mock strategy uses only provided brand context and needs human validation."],
            "approval_required": True,
        }

