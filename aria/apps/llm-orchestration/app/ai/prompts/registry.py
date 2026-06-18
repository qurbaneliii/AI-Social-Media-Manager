from __future__ import annotations

import json
from dataclasses import dataclass

from ai.llm.types import LLMMessage
from ai.schemas.content import ContentRequest, GeneratedContentPackage

from .platform_prompts import PLATFORM_ADAPTATION_PROMPT_V1
from .system_prompts import BRAND_SYSTEM_PROMPT_V1
from .task_prompts import (
    BRAND_STRATEGY_PROMPT_V1,
    CALENDAR_PLANNING_PROMPT_V1,
    COMMUNITY_MANAGEMENT_PROMPT_V1,
    COMPETITOR_ANALYSIS_PROMPT_V1,
    CONTENT_GENERATION_PROMPT_V1,
    HASHTAG_RECOMMENDATION_PROMPT_V1,
    QUALITY_REVIEW_PROMPT_V1,
    REPORTING_INSIGHT_PROMPT_V1,
    TREND_RESEARCH_PROMPT_V1,
    VISUAL_CONCEPT_PROMPT_V1,
)


@dataclass(frozen=True)
class PromptTemplate:
    key: str
    version: str
    content: str


class PromptRegistry:
    """Versioned prompt access point for orchestration and agents."""

    def __init__(self) -> None:
        self._templates = {
            "brand_system:v1": PromptTemplate("brand_system", "v1", BRAND_SYSTEM_PROMPT_V1),
            "platform_adaptation:v1": PromptTemplate("platform_adaptation", "v1", PLATFORM_ADAPTATION_PROMPT_V1),
            "content_generation:v1": PromptTemplate("content_generation", "v1", CONTENT_GENERATION_PROMPT_V1),
            "quality_review:v1": PromptTemplate("quality_review", "v1", QUALITY_REVIEW_PROMPT_V1),
            "brand_strategy:v1": PromptTemplate("brand_strategy", "v1", BRAND_STRATEGY_PROMPT_V1),
            "competitor_analysis:v1": PromptTemplate("competitor_analysis", "v1", COMPETITOR_ANALYSIS_PROMPT_V1),
            "trend_research:v1": PromptTemplate("trend_research", "v1", TREND_RESEARCH_PROMPT_V1),
            "hashtag_recommendation:v1": PromptTemplate(
                "hashtag_recommendation", "v1", HASHTAG_RECOMMENDATION_PROMPT_V1
            ),
            "visual_concept:v1": PromptTemplate("visual_concept", "v1", VISUAL_CONCEPT_PROMPT_V1),
            "calendar_planning:v1": PromptTemplate("calendar_planning", "v1", CALENDAR_PLANNING_PROMPT_V1),
            "community_management:v1": PromptTemplate(
                "community_management", "v1", COMMUNITY_MANAGEMENT_PROMPT_V1
            ),
            "reporting_insight:v1": PromptTemplate("reporting_insight", "v1", REPORTING_INSIGHT_PROMPT_V1),
        }

    def get(self, key: str, version: str = "v1") -> PromptTemplate:
        prompt_key = f"{key}:{version}"
        if prompt_key not in self._templates:
            raise KeyError(f"Prompt template not found: {prompt_key}")
        return self._templates[prompt_key]

    def build_content_generation_messages(self, request: ContentRequest) -> list[LLMMessage]:
        context = {
            "brand_profile": request.brand_profile.model_dump(),
            "platform_context": request.platform_context.model_dump(),
            "campaign_objective": request.campaign_objective,
            "topic": request.topic,
            "content_pillar": request.content_pillar,
            "language": request.language,
            "number_of_variants": request.number_of_variants,
            "extra_context": request.extra_context,
        }
        return [
            LLMMessage(role="system", content=self.get("brand_system").content),
            LLMMessage(role="system", content=self.get("platform_adaptation").content),
            LLMMessage(role="user", content=f"{self.get('content_generation').content}\n\nContext JSON:\n{json.dumps(context)}"),
        ]

    def build_quality_review_messages(
        self,
        request: ContentRequest,
        package: GeneratedContentPackage,
    ) -> list[LLMMessage]:
        payload = {
            "brand_profile": request.brand_profile.model_dump(),
            "platform_context": request.platform_context.model_dump(),
            "generated_content_package": package.model_dump(mode="json", exclude={"quality_scores"}),
        }
        return [
            LLMMessage(role="system", content=self.get("brand_system").content),
            LLMMessage(role="user", content=f"{self.get('quality_review').content}\n\nReview JSON:\n{json.dumps(payload)}"),
        ]

    def build_agent_messages(self, prompt_key: str, payload: dict) -> list[LLMMessage]:
        return [
            LLMMessage(role="system", content=self.get("brand_system").content),
            LLMMessage(role="system", content=self.get("platform_adaptation").content),
            LLMMessage(role="user", content=f"{self.get(prompt_key).content}\n\nContext JSON:\n{json.dumps(payload, default=str)}"),
        ]
