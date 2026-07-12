from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .schemas import ApprovalAuditEvent, ApprovalDecision, ApprovalObjectType


class DraftListFilters(BaseModel):
    brand_id: str | None = None
    status: str | None = None
    object_type: ApprovalObjectType | None = None
    platform: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    created_after: datetime | None = None
    created_before: datetime | None = None


class ApprovalQueueItem(BaseModel):
    object_id: str
    object_type: ApprovalObjectType
    brand_id: str
    approval_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ContentDraftQueueItem(ApprovalQueueItem):
    draft_id: str
    platform: str
    content_type: str
    topic: str
    hook_preview: str
    caption_preview: str
    requires_human_review: bool = True
    risk_summary: list[str] = Field(default_factory=list)
    quality_score_summary: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    mock_mode: bool | None = None


class CalendarDraftQueueItem(ApprovalQueueItem):
    item_id: str
    platform: str
    planned_date: str | None = None
    planned_time: str | None = None
    content_pillar: str = ""
    objective: str = ""
    topic: str = ""
    readiness_status: str | None = None


class CommunityReplyQueueItem(ApprovalQueueItem):
    reply_draft_id: str
    original_message_preview: str
    suggested_reply_preview: str
    sentiment: str
    intent: str
    urgency: str
    toxicity_risk: float
    crisis_risk: float
    requires_human_review: bool = True
    escalation_reason: str | None = None
    auto_reply_allowed: bool = False


class ReportDraftQueueItem(ApprovalQueueItem):
    report_id: str
    report_type: str
    date_range: str = ""
    summary_preview: str = ""


QueueItem = ContentDraftQueueItem | CalendarDraftQueueItem | CommunityReplyQueueItem | ReportDraftQueueItem


class ApprovalQueueResponse(BaseModel):
    items: list[QueueItem]
    count: int
    limit: int
    offset: int


class ContentApprovalQueueResponse(BaseModel):
    items: list[ContentDraftQueueItem]
    count: int
    limit: int
    offset: int


class CalendarApprovalQueueResponse(BaseModel):
    items: list[CalendarDraftQueueItem]
    count: int
    limit: int
    offset: int


class CommunityApprovalQueueResponse(BaseModel):
    items: list[CommunityReplyQueueItem]
    count: int
    limit: int
    offset: int


class ReportApprovalQueueResponse(BaseModel):
    items: list[ReportDraftQueueItem]
    count: int
    limit: int
    offset: int


class ApprovalAuditEventResponse(ApprovalAuditEvent):
    pass


class ApprovalAuditTimeline(BaseModel):
    object_id: str
    object_type: ApprovalObjectType
    events: list[ApprovalAuditEvent] = Field(default_factory=list)
    latest_requested_changes: list[str] = Field(default_factory=list)
    last_review_reason: str = ""


class ContentDraftDetail(BaseModel):
    draft_id: str
    object_type: ApprovalObjectType = ApprovalObjectType.CONTENT_DRAFT
    brand_id: str
    platform: str
    content_type: str
    topic: str
    hook: str = ""
    caption: str = ""
    cta: str = ""
    hashtags: list[str] = Field(default_factory=list)
    visual_brief_summary: str = ""
    video_script_summary: str = ""
    carousel_structure_summary: list[str] = Field(default_factory=list)
    posting_recommendation: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    risk_summary: list[str] = Field(default_factory=list)
    quality_score_summary: dict[str, Any] = Field(default_factory=dict)
    approval_status: str
    requires_human_review: bool = True
    model: str | None = None
    mock_mode: bool | None = None
    prompt_version: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    latest_audit_events: list[ApprovalAuditEvent] = Field(default_factory=list)
    last_requested_changes: list[str] = Field(default_factory=list)
    last_review_reason: str = ""


class CalendarDraftDetail(BaseModel):
    item_id: str
    object_type: ApprovalObjectType = ApprovalObjectType.CALENDAR_DRAFT
    brand_id: str
    platform: str
    planned_date: str | None = None
    planned_time: str | None = None
    content_pillar: str = ""
    objective: str = ""
    topic: str = ""
    content_type: str = ""
    rationale: str = ""
    approval_status: str
    readiness_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    latest_audit_events: list[ApprovalAuditEvent] = Field(default_factory=list)
    last_requested_changes: list[str] = Field(default_factory=list)
    last_review_reason: str = ""


class CommunityReplyDraftDetail(BaseModel):
    reply_draft_id: str
    object_type: ApprovalObjectType = ApprovalObjectType.COMMUNITY_REPLY
    brand_id: str
    original_message_text: str
    suggested_reply: str
    sentiment: str
    intent: str
    urgency: str
    toxicity_risk: float
    crisis_risk: float
    confidence: float
    requires_human_review: bool = True
    escalation_reason: str | None = None
    auto_reply_allowed: bool = False
    approval_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    latest_audit_events: list[ApprovalAuditEvent] = Field(default_factory=list)
    last_requested_changes: list[str] = Field(default_factory=list)
    last_review_reason: str = ""


class ReportDraftDetail(BaseModel):
    report_id: str
    object_type: ApprovalObjectType = ApprovalObjectType.REPORT_DRAFT
    brand_id: str
    report_type: str
    date_range: str = ""
    summary: str = ""
    key_insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    approval_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    latest_audit_events: list[ApprovalAuditEvent] = Field(default_factory=list)
    last_requested_changes: list[str] = Field(default_factory=list)
    last_review_reason: str = ""


ApprovalDetail = ContentDraftDetail | CalendarDraftDetail | CommunityReplyDraftDetail | ReportDraftDetail


def content_queue_item_from_row(row: dict[str, Any]) -> ContentDraftQueueItem:
    package = _jsonish(row.get("content_package_json"))
    quality = _jsonish(row.get("quality_scores_json"))
    posting = _jsonish(package.get("posting_recommendation"))
    risks = package.get("risks") or []
    requires_review = bool(posting.get("approval_required", True))
    if quality.get("approval_status") == "requires_human_review":
        requires_review = True
    draft_id = str(row.get("draft_id"))
    return ContentDraftQueueItem(
        object_id=draft_id,
        object_type=ApprovalObjectType.CONTENT_DRAFT,
        draft_id=draft_id,
        brand_id=row.get("brand_id", ""),
        platform=row.get("platform", ""),
        content_type=row.get("content_type", ""),
        topic=row.get("topic", ""),
        hook_preview=_preview(package.get("hook", "")),
        caption_preview=_preview(package.get("caption", "")),
        approval_status=row.get("approval_status", "draft"),
        requires_human_review=requires_review,
        risk_summary=[str(risk) for risk in risks[:5]],
        quality_score_summary=_quality_summary(quality),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        model=row.get("model"),
        mock_mode=row.get("mock_mode"),
    )


def calendar_queue_item_from_row(row: dict[str, Any]) -> CalendarDraftQueueItem:
    item = _jsonish(row.get("calendar_item_json"))
    item_id = str(row.get("calendar_item_id"))
    return CalendarDraftQueueItem(
        object_id=item_id,
        object_type=ApprovalObjectType.CALENDAR_DRAFT,
        item_id=item_id,
        brand_id=row.get("brand_id", ""),
        platform=row.get("platform", item.get("platform", "")),
        planned_date=str(row.get("scheduled_date") or item.get("date") or ""),
        planned_time=str(row.get("scheduled_time") or item.get("time") or ""),
        content_pillar=item.get("content_pillar", ""),
        objective=item.get("objective", ""),
        topic=item.get("topic", ""),
        approval_status=row.get("approval_status") or row.get("draft_status") or "draft",
        readiness_status=row.get("draft_status"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def community_queue_item_from_row(row: dict[str, Any]) -> CommunityReplyQueueItem:
    reply_draft_id = str(row.get("reply_draft_id"))
    return CommunityReplyQueueItem(
        object_id=reply_draft_id,
        object_type=ApprovalObjectType.COMMUNITY_REPLY,
        reply_draft_id=reply_draft_id,
        brand_id=row.get("brand_id", ""),
        original_message_preview=_preview(row.get("original_message_text", "")),
        suggested_reply_preview=_preview(row.get("suggested_reply", "")),
        sentiment=row.get("sentiment", ""),
        intent=row.get("intent", ""),
        urgency=row.get("urgency", ""),
        toxicity_risk=float(row.get("toxicity_risk") or 0.0),
        crisis_risk=float(row.get("crisis_risk") or 0.0),
        requires_human_review=bool(row.get("requires_human_review", True)),
        escalation_reason=row.get("escalation_reason"),
        auto_reply_allowed=False,
        approval_status=row.get("approval_status", "draft"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def report_queue_item_from_row(row: dict[str, Any]) -> ReportDraftQueueItem:
    payload = _jsonish(row.get("insight_payload_json"))
    report_id = str(row.get("report_draft_id"))
    return ReportDraftQueueItem(
        object_id=report_id,
        object_type=ApprovalObjectType.REPORT_DRAFT,
        report_id=report_id,
        brand_id=row.get("brand_id", ""),
        report_type=row.get("report_type", ""),
        date_range=row.get("date_range", ""),
        summary_preview=_preview(payload.get("summary", "")),
        approval_status=row.get("approval_status") or row.get("review_status") or "draft",
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def audit_timeline_from_events(
    object_type: ApprovalObjectType,
    object_id: str,
    events: list[ApprovalAuditEvent | ApprovalDecision],
) -> ApprovalAuditTimeline:
    normalized_events = [
        event if isinstance(event, ApprovalAuditEvent) else ApprovalAuditEvent.model_validate(event.model_dump(mode="json"))
        for event in events
    ]
    latest_change_event = next((event for event in reversed(normalized_events) if event.requested_changes), None)
    latest_reason_event = next((event for event in reversed(normalized_events) if event.reason), None)
    return ApprovalAuditTimeline(
        object_id=object_id,
        object_type=object_type,
        events=normalized_events,
        latest_requested_changes=latest_change_event.requested_changes if latest_change_event else [],
        last_review_reason=latest_reason_event.reason if latest_reason_event else "",
    )


def content_detail_from_row(row: dict[str, Any], events: list[ApprovalAuditEvent] | None = None) -> ContentDraftDetail:
    package = _jsonish(row.get("content_package_json"))
    quality = _jsonish(row.get("quality_scores_json"))
    audit = _jsonish(row.get("audit_metadata_json"))
    posting = _jsonish(package.get("posting_recommendation"))
    event_list = events or []
    timeline = audit_timeline_from_events(ApprovalObjectType.CONTENT_DRAFT, str(row.get("draft_id")), event_list)
    return ContentDraftDetail(
        draft_id=str(row.get("draft_id")),
        brand_id=row.get("brand_id", ""),
        platform=row.get("platform", package.get("platform", "")),
        content_type=row.get("content_type", package.get("content_type", "")),
        topic=row.get("topic", ""),
        hook=str(package.get("hook", "")),
        caption=str(package.get("caption", "")),
        cta=str(package.get("cta", "")),
        hashtags=[str(tag) for tag in package.get("hashtags", [])],
        visual_brief_summary=_summarize_mapping(package.get("visual_brief")),
        video_script_summary=_preview(package.get("video_script", ""), 240),
        carousel_structure_summary=_summarize_carousel(package.get("carousel_structure")),
        posting_recommendation=posting,
        rationale=str(package.get("rationale", "")),
        risk_summary=[str(risk) for risk in package.get("risks", [])],
        quality_score_summary=_quality_summary(quality),
        approval_status=row.get("approval_status", "draft"),
        requires_human_review=_requires_review(posting, quality),
        model=row.get("model") or audit.get("model"),
        mock_mode=row.get("mock_mode") if row.get("mock_mode") is not None else audit.get("mock_mode"),
        prompt_version=row.get("prompt_version") or audit.get("prompt_version"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        latest_audit_events=timeline.events[-10:],
        last_requested_changes=timeline.latest_requested_changes,
        last_review_reason=timeline.last_review_reason,
    )


def calendar_detail_from_row(row: dict[str, Any], events: list[ApprovalAuditEvent] | None = None) -> CalendarDraftDetail:
    item = _jsonish(row.get("calendar_item_json"))
    event_list = events or []
    item_id = str(row.get("calendar_item_id"))
    timeline = audit_timeline_from_events(ApprovalObjectType.CALENDAR_DRAFT, item_id, event_list)
    return CalendarDraftDetail(
        item_id=item_id,
        brand_id=row.get("brand_id", ""),
        platform=row.get("platform", item.get("platform", "")),
        planned_date=str(row.get("scheduled_date") or item.get("date") or ""),
        planned_time=str(row.get("scheduled_time") or item.get("time") or ""),
        content_pillar=item.get("content_pillar", ""),
        objective=item.get("objective", ""),
        topic=item.get("topic", ""),
        content_type=item.get("content_type", ""),
        rationale=item.get("rationale", ""),
        approval_status=row.get("approval_status") or row.get("draft_status") or "draft",
        readiness_status=row.get("draft_status"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        latest_audit_events=timeline.events[-10:],
        last_requested_changes=timeline.latest_requested_changes,
        last_review_reason=timeline.last_review_reason,
    )


def community_detail_from_row(
    row: dict[str, Any],
    events: list[ApprovalAuditEvent] | None = None,
) -> CommunityReplyDraftDetail:
    event_list = events or []
    reply_draft_id = str(row.get("reply_draft_id"))
    timeline = audit_timeline_from_events(ApprovalObjectType.COMMUNITY_REPLY, reply_draft_id, event_list)
    return CommunityReplyDraftDetail(
        reply_draft_id=reply_draft_id,
        brand_id=row.get("brand_id", ""),
        original_message_text=row.get("original_message_text", ""),
        suggested_reply=row.get("suggested_reply", ""),
        sentiment=row.get("sentiment", ""),
        intent=row.get("intent", ""),
        urgency=row.get("urgency", ""),
        toxicity_risk=float(row.get("toxicity_risk") or 0.0),
        crisis_risk=float(row.get("crisis_risk") or 0.0),
        confidence=float(row.get("confidence") or 0.0),
        requires_human_review=bool(row.get("requires_human_review", True)),
        escalation_reason=row.get("escalation_reason"),
        auto_reply_allowed=False,
        approval_status=row.get("approval_status", "draft"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        latest_audit_events=timeline.events[-10:],
        last_requested_changes=timeline.latest_requested_changes,
        last_review_reason=timeline.last_review_reason,
    )


def report_detail_from_row(row: dict[str, Any], events: list[ApprovalAuditEvent] | None = None) -> ReportDraftDetail:
    payload = _jsonish(row.get("insight_payload_json"))
    recommendations = _json_list(row.get("recommendations_json"))
    event_list = events or []
    report_id = str(row.get("report_draft_id"))
    timeline = audit_timeline_from_events(ApprovalObjectType.REPORT_DRAFT, report_id, event_list)
    return ReportDraftDetail(
        report_id=report_id,
        brand_id=row.get("brand_id", ""),
        report_type=row.get("report_type", ""),
        date_range=row.get("date_range", ""),
        summary=str(payload.get("summary", "")),
        key_insights=_report_key_insights(payload),
        recommendations=[str(item) for item in recommendations],
        approval_status=row.get("approval_status") or row.get("review_status") or "draft",
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        latest_audit_events=timeline.events[-10:],
        last_requested_changes=timeline.latest_requested_changes,
        last_review_reason=timeline.last_review_reason,
    )


def _jsonish(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _preview(value: Any, limit: int = 160) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def _requires_review(posting: dict[str, Any], quality: dict[str, Any]) -> bool:
    requires_review = bool(posting.get("approval_required", True))
    if quality.get("approval_status") in {"requires_human_review", "needs_revision"}:
        requires_review = True
    return requires_review


def _summarize_mapping(value: Any) -> str:
    data = _jsonish(value)
    if not data:
        return ""
    preferred_keys = ("summary", "concept", "description", "direction", "scene", "layout", "mood")
    parts = [str(data[key]) for key in preferred_keys if data.get(key)]
    if parts:
        return _preview(" | ".join(parts), 260)
    return _preview("; ".join(f"{key}: {val}" for key, val in data.items()), 260)


def _summarize_carousel(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    summaries: list[str] = []
    for index, slide in enumerate(value[:8], start=1):
        if isinstance(slide, dict):
            title = slide.get("title") or slide.get("headline") or slide.get("hook") or f"Slide {index}"
            body = slide.get("body") or slide.get("description") or slide.get("copy") or ""
            summaries.append(_preview(f"{title}: {body}" if body else title, 180))
        else:
            summaries.append(_preview(slide, 180))
    return summaries


def _report_key_insights(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("key_insights", "what_worked", "what_failed", "next_experiments", "risk_notes"):
        raw = payload.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
    return values[:12]


def _quality_summary(quality: dict[str, Any]) -> dict[str, Any]:
    return {
        key: quality[key]
        for key in (
            "brand_consistency_score",
            "platform_fit_score",
            "clarity_score",
            "factual_risk_score",
            "safety_risk_score",
            "engagement_potential_score",
            "approval_status",
        )
        if key in quality
    }
