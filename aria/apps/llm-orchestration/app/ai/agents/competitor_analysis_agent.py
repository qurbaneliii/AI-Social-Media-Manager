from __future__ import annotations

from ai.schemas.competitor import CompetitorAnalysisRequest, CompetitorInsightReport

from .base import BaseAgent


class CompetitorAnalysisAgent(BaseAgent):
    async def analyze(self, request: CompetitorAnalysisRequest) -> CompetitorInsightReport:
        messages = self.prompt_registry.build_agent_messages(
            "competitor_analysis",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            CompetitorInsightReport,
            mock_factory=lambda: self._mock_report(request),
        )

    def _mock_report(self, request: CompetitorAnalysisRequest) -> dict:
        content_types = [post.content_type for post in request.competitors] or ["provided posts"]
        hashtags = [tag for post in request.competitors for tag in post.hashtags]
        return {
            "top_performing_content_types": list(dict.fromkeys(content_types))[:3],
            "hook_patterns": ["Lead with a concrete business pain or measurable outcome."],
            "recurring_themes": ["Education", "proof", "workflow improvement"],
            "hashtag_patterns": list(dict.fromkeys(hashtags))[:8] or ["No hashtag data provided."],
            "tone_patterns": ["Clear", "practical", "outcome-focused"],
            "posting_patterns": ["Posting pattern analysis is limited to provided timestamps."],
            "content_gaps": ["Create brand-specific proof assets competitors do not cover."],
            "strategic_opportunities": ["Turn competitor themes into differentiated, approval-based campaigns."],
            "risk_notes": ["Do not claim market superiority without verified evidence."],
            "source_limitations": ["No scraping or external social API data was used."],
        }

