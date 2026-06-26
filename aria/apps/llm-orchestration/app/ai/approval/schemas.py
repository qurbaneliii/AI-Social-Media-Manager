from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ApprovalObjectType(StrEnum):
    CONTENT_DRAFT = "content_draft"
    CALENDAR_DRAFT = "calendar_draft"
    COMMUNITY_REPLY = "community_reply"
    REPORT_DRAFT = "report_draft"


class ApprovalStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    ARCHIVED = "archived"
    READY_FOR_SCHEDULING = "ready_for_scheduling"
    ESCALATED = "escalated"


class QualityReviewStatus(StrEnum):
    GENERATED = "generated"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"


class ApprovalAction(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ARCHIVE = "archive"
    MARK_READY_FOR_SCHEDULING = "mark_ready_for_scheduling"
    ESCALATE = "escalate"
    RESET_TO_DRAFT = "reset_to_draft"


class DraftLifecycleMetadata(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    prompt_version: str | None = None
    model: str | None = None
    mock_mode: bool | None = None
    quality_scores: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    object_id: str
    object_type: ApprovalObjectType
    previous_status: ApprovalStatus | None = None
    new_status: ApprovalStatus
    action: ApprovalAction
    reviewer_id: str | None = None
    reviewer_role: str | None = None
    reason: str = ""
    requested_changes: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("new_status")
    @classmethod
    def forbidden_terminal_runtime_states(cls, value: ApprovalStatus) -> ApprovalStatus:
        if value.value in {"published", "scheduled", "sent"}:
            raise ValueError("Approval lifecycle cannot publish, schedule, or send objects.")
        return value


class ApprovalAuditEvent(ApprovalDecision):
    event_id: str | None = None


class ApprovalResult(BaseModel):
    decision: ApprovalDecision
    audit_event: ApprovalAuditEvent
    record: dict[str, Any] = Field(default_factory=dict)


class ContentDraftRecord(BaseModel):
    draft_id: str
    brand_id: str
    platform: str
    content_type: str
    topic: str
    content_package: dict[str, Any]
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    quality_scores: dict[str, Any] = Field(default_factory=dict)
    lifecycle: DraftLifecycleMetadata = Field(default_factory=DraftLifecycleMetadata)


class CalendarDraftRecord(BaseModel):
    calendar_item_id: str
    brand_id: str
    platform: str
    calendar_item: dict[str, Any]
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    approval_required: bool = True
    lifecycle: DraftLifecycleMetadata = Field(default_factory=DraftLifecycleMetadata)


class CommunityReplyDraftRecord(BaseModel):
    reply_draft_id: str
    brand_id: str
    original_message_text: str
    sentiment: str
    intent: str
    urgency: str
    toxicity_risk: float = Field(ge=0.0, le=1.0)
    crisis_risk: float = Field(ge=0.0, le=1.0)
    suggested_reply: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True
    escalation_reason: str | None = None
    auto_reply_allowed: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    lifecycle: DraftLifecycleMetadata = Field(default_factory=DraftLifecycleMetadata)

    @field_validator("auto_reply_allowed")
    @classmethod
    def auto_reply_must_remain_disabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("Community replies cannot be auto-sent in Phase 4.")
        return value


class ReportDraftRecord(BaseModel):
    report_draft_id: str
    brand_id: str
    report_type: str
    date_range: str = ""
    insight_payload: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    lifecycle: DraftLifecycleMetadata = Field(default_factory=DraftLifecycleMetadata)
