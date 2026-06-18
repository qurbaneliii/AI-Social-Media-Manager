from __future__ import annotations

from ai.schemas.community import CommunityManagementRequest, CommunityMessageAnalysis

from .base import BaseAgent


class CommunityManagementAgent(BaseAgent):
    async def analyze(self, request: CommunityManagementRequest) -> CommunityMessageAnalysis:
        messages = self.prompt_registry.build_agent_messages(
            "community_management",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            CommunityMessageAnalysis,
            mock_factory=lambda: self._mock_analysis(request),
        )

    def _mock_analysis(self, request: CommunityManagementRequest) -> dict:
        text = request.message_text.lower()
        is_risky = any(term in text for term in ["refund", "angry", "lawsuit", "unsafe", "scam", "urgent"])
        is_buying = any(term in text for term in ["price", "buy", "demo", "trial"])
        is_faq = "?" in request.message_text
        return {
            "message_text": request.message_text,
            "sentiment": "negative" if is_risky else "neutral",
            "intent": "complaint" if is_risky else "question" if is_faq else "general",
            "urgency": "high" if is_risky else "normal",
            "toxicity_risk": 0.35 if is_risky else 0.05,
            "crisis_risk": 0.4 if is_risky else 0.03,
            "complaint_type": "support" if is_risky else None,
            "buying_intent": is_buying,
            "faq_intent": is_faq,
            "suggested_reply": (
                f"Thanks for reaching out. {request.brand_profile.brand_name} will review this and respond carefully."
            ),
            "confidence": 0.72,
            "requires_human_review": True,
            "escalation_reason": "Risky or customer-facing replies require human approval.",
            "auto_reply_allowed": False,
        }

