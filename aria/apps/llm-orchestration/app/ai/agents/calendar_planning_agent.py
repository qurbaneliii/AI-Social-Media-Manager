from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from ai.schemas.calendar import CalendarPlanningRequest, ContentCalendarPlan

from .base import BaseAgent


class CalendarPlanningAgent(BaseAgent):
    async def create_calendar(self, request: CalendarPlanningRequest) -> ContentCalendarPlan:
        messages = self.prompt_registry.build_agent_messages(
            "calendar_planning",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            ContentCalendarPlan,
            mock_factory=lambda: self._mock_calendar(request),
        )

    def _mock_calendar(self, request: CalendarPlanningRequest) -> dict:
        platforms = request.platforms or request.brand_profile.platforms or ["linkedin"]
        pillars = request.content_pillars or ["education", "proof", "community"]
        objectives = request.campaign_objectives or request.brand_profile.business_goals or ["build trust"]
        content_types = request.preferred_content_types or ["post", "carousel", "short_video"]
        days = max((request.end_date - request.start_date).days + 1, 1)
        item_count = min(request.posting_frequency_per_week, days, 7)
        items = []
        for index in range(item_count):
            scheduled_date = request.start_date + timedelta(days=index)
            items.append(
                {
                    "date": scheduled_date.isoformat(),
                    "time": time(hour=9 + (index % 4), minute=0).isoformat(),
                    "platform": platforms[index % len(platforms)],
                    "content_pillar": pillars[index % len(pillars)],
                    "objective": objectives[index % len(objectives)],
                    "topic": f"{pillars[index % len(pillars)].title()} angle {index + 1}",
                    "content_type": content_types[index % len(content_types)],
                    "draft_status": "draft",
                    "rationale": "Mock calendar balances provided pillars, platforms, and objectives.",
                    "approval_required": True,
                }
            )
        return {
            "items": items,
            "rationale": f"Draft calendar generated at {datetime.now(UTC).date().isoformat()} for planning review.",
            "risk_notes": ["Suggested times are placeholders until audience timing data is connected."],
            "approval_required": True,
        }
