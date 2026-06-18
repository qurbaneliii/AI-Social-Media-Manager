from __future__ import annotations

from typing import Any

from ai.llm.types import LLMMessage
from ai.schemas.content import ContentRequest, GeneratedContentPackage
from ai.schemas.evaluation import AIQualityReview

from .base import BaseAgent


class QualityReviewAgent(BaseAgent):
    async def review(self, request: ContentRequest, package: GeneratedContentPackage) -> AIQualityReview:
        messages = self.prompt_registry.build_quality_review_messages(request, package)
        return await self.llm_client.generate_structured(
            messages,
            AIQualityReview,
            mock_factory=lambda: self._mock_review(package),
        )

    def _mock_review(self, package: GeneratedContentPackage) -> dict:
        needs_review = bool(package.risks)
        return {
            "brand_consistency_score": 0.78,
            "platform_fit_score": 0.76,
            "clarity_score": 0.82,
            "cta_strength_score": 0.72,
            "originality_score": 0.68,
            "factual_risk_score": 0.15,
            "safety_risk_score": 0.12,
            "engagement_potential_score": 0.7,
            "approval_status": "requires_human_review" if needs_review else "approved",
            "improvement_notes": [
                "Confirm claims against approved brand facts.",
                "Tighten the CTA before final approval.",
            ],
        }

    async def review_structured_output(self, payload: dict[str, Any]) -> AIQualityReview:
        messages = [
            LLMMessage(role="system", content=self.prompt_registry.get("brand_system").content),
            LLMMessage(
                role="user",
                content=(
                    f"{self.prompt_registry.get('quality_review').content}\n\n"
                    f"Review JSON:\n{payload}"
                ),
            ),
        ]
        return await self.llm_client.generate_structured(
            messages,
            AIQualityReview,
            mock_factory=lambda: {
                "brand_consistency_score": 0.75,
                "platform_fit_score": 0.74,
                "clarity_score": 0.78,
                "cta_strength_score": 0.65,
                "originality_score": 0.68,
                "factual_risk_score": 0.2,
                "safety_risk_score": 0.18,
                "engagement_potential_score": 0.7,
                "approval_status": "requires_human_review",
                "improvement_notes": ["Structured agent output requires human approval before external use."],
            },
        )
