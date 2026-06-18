from __future__ import annotations

from ai.schemas.trend import TrendInsightReport, TrendResearchRequest

from .base import BaseAgent


class TrendResearchAgent(BaseAgent):
    async def research(self, request: TrendResearchRequest) -> TrendInsightReport:
        messages = self.prompt_registry.build_agent_messages(
            "trend_research",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            TrendInsightReport,
            mock_factory=lambda: self._mock_report(request),
        )

    def _mock_report(self, request: TrendResearchRequest) -> dict:
        keywords = [trend.keyword for trend in request.trends] or [request.business_goal or "brand growth"]
        platforms = request.platforms or request.brand_profile.platforms or ["linkedin"]
        return {
            "relevant_topics": keywords,
            "recommended_hashtags": [f"#{keyword.replace(' ', '')}" for keyword in keywords[:5]],
            "content_formats": ["short educational post", "carousel", "behind-the-scenes proof point"],
            "trend_opportunities": [f"Connect {keywords[0]} to a brand-safe customer problem."],
            "platform_notes": {platform: ["Adapt format and pacing before publishing."] for platform in platforms},
            "risk_notes": ["Trend relevance is based only on provided data."],
            "source_limitations": ["No browsing, scraping, or live trend API was used."],
        }

