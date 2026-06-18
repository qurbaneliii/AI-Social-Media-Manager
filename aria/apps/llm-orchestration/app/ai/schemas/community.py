from __future__ import annotations

from pydantic import BaseModel, Field

from .brand import BrandProfile


class CommunityManagementRequest(BaseModel):
    brand_profile: BrandProfile
    platform: str
    message_text: str
    author_context: dict[str, str] = Field(default_factory=dict)
    conversation_context: list[str] = Field(default_factory=list)


class CommunityMessageAnalysis(BaseModel):
    message_text: str
    sentiment: str
    intent: str
    urgency: str
    toxicity_risk: float = Field(ge=0.0, le=1.0)
    crisis_risk: float = Field(ge=0.0, le=1.0)
    complaint_type: str | None = None
    buying_intent: bool = False
    faq_intent: bool = False
    suggested_reply: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True
    escalation_reason: str | None = None
    auto_reply_allowed: bool = False
