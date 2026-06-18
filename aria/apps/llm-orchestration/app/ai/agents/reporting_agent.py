from __future__ import annotations

from ai.schemas.analytics import ReportingInsightReport, ReportingInsightRequest

from .base import BaseAgent


class ReportingAgent(BaseAgent):
    async def generate_insights(self, request: ReportingInsightRequest) -> ReportingInsightReport:
        messages = self.prompt_registry.build_agent_messages(
            "reporting_insight",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            ReportingInsightReport,
            mock_factory=lambda: self._mock_report(request),
        )

    def _mock_report(self, request: ReportingInsightRequest) -> dict:
        platforms = ", ".join(request.platforms) or "provided platforms"
        return {
            "summary": f"Mock report for {request.reporting_period} across {platforms}.",
            "what_worked": ["Identify posts with above-average engagement in the provided analytics."],
            "what_failed": ["Flag formats with low completion or low save/share rates."],
            "recommended_changes": ["Shift more drafts toward the highest-performing pillar after approval."],
            "next_experiments": ["Test one educational carousel and one proof-led short video."],
            "risk_notes": ["Insights are limited to provided analytics data."],
            "chart_ready_data": request.analytics_data,
        }

