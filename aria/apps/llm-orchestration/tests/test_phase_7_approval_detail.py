from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from ai.approval import ApprovalDecision
from ai.approval.service import ApprovalService
from ai.approval.queue import content_detail_from_row


def _now() -> datetime:
    return datetime.now(UTC)


def _content_row(status: str = "in_review") -> dict[str, Any]:
    return {
        "draft_id": "content-1",
        "brand_id": "brand-1",
        "platform": "linkedin",
        "content_type": "post",
        "topic": "approval detail DTOs",
        "content_package_json": {
            "platform": "linkedin",
            "content_type": "post",
            "hook": "A precise hook.",
            "caption": "A safe full caption for human review.",
            "cta": "Review the draft",
            "hashtags": ["#AI", "#Approval"],
            "visual_brief": {"direction": "Clean product UI screenshot", "mood": "calm"},
            "video_script": "Intro, problem, approval-safe resolution.",
            "carousel_structure": [{"title": "Why review matters", "body": "Human control stays central."}],
            "posting_recommendation": {"approval_required": True, "best_window": "morning"},
            "rationale": "Matches the brand strategy.",
            "risks": ["Needs source verification"],
        },
        "quality_scores_json": {
            "brand_consistency_score": 0.91,
            "platform_fit_score": 0.87,
            "clarity_score": 0.89,
            "factual_risk_score": 0.22,
            "safety_risk_score": 0.05,
            "engagement_potential_score": 0.74,
            "approval_status": "requires_human_review",
        },
        "audit_metadata_json": {"prompt_version": "v1", "model": "gpt-4o-mini", "mock_mode": True},
        "approval_status": status,
        "prompt_version": "v1",
        "model": "gpt-4o-mini",
        "mock_mode": True,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _calendar_row(status: str = "draft") -> dict[str, Any]:
    return {
        "calendar_item_id": "calendar-1",
        "brand_id": "brand-1",
        "platform": "linkedin",
        "scheduled_date": "2026-06-28",
        "scheduled_time": "09:00:00",
        "approval_status": status,
        "draft_status": status,
        "calendar_item_json": {
            "content_pillar": "education",
            "objective": "build trust",
            "topic": "approval reviews",
            "content_type": "carousel",
            "rationale": "Balances weekly content pillars.",
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


def _community_row(status: str = "draft") -> dict[str, Any]:
    return {
        "reply_draft_id": "reply-1",
        "brand_id": "brand-1",
        "original_message_text": "Can someone help me with billing?",
        "suggested_reply": "Thanks for reaching out. A team member will review this and help.",
        "sentiment": "neutral",
        "intent": "support_request",
        "urgency": "medium",
        "toxicity_risk": 0.0,
        "crisis_risk": 0.0,
        "confidence": 0.93,
        "requires_human_review": True,
        "escalation_reason": None,
        "auto_reply_allowed": False,
        "approval_status": status,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _report_row(status: str = "draft") -> dict[str, Any]:
    return {
        "report_draft_id": "report-1",
        "brand_id": "brand-1",
        "report_type": "weekly",
        "date_range": "2026-06-20..2026-06-27",
        "insight_payload_json": {
            "summary": "Approval-safe posts improved engagement.",
            "what_worked": ["Educational posts"],
            "next_experiments": ["Test shorter captions"],
        },
        "recommendations_json": ["Review high-risk claims before reuse"],
        "approval_status": status,
        "created_at": _now(),
        "updated_at": _now(),
    }


class DetailRepository:
    def __init__(self) -> None:
        self.content = {"content-1": _content_row()}
        self.calendar = {"calendar-1": _calendar_row()}
        self.community = {"reply-1": _community_row()}
        self.report = {"report-1": _report_row()}
        self.audit_events: list[dict[str, Any]] = [
            {
                "event_id": "event-1",
                "object_id": "content-1",
                "object_type": "content_draft",
                "previous_status": "draft",
                "new_status": "in_review",
                "action": "submit",
                "reviewer_id": "reviewer-1",
                "reviewer_role": "brand_manager",
                "reason": "Submitted for review.",
                "requested_changes": [],
                "timestamp": _now(),
                "metadata": {},
            }
        ]

    async def get_content_draft_by_id(self, draft_id: str) -> dict[str, Any] | None:
        return self.content.get(draft_id)

    async def update_content_draft_approval_status(self, draft_id: str, status: str) -> dict[str, Any]:
        self.content[draft_id]["approval_status"] = status
        self.content[draft_id]["updated_at"] = _now()
        return self.content[draft_id]

    async def get_calendar_draft_item_by_id(self, calendar_item_id: str) -> dict[str, Any] | None:
        return self.calendar.get(calendar_item_id)

    async def update_calendar_draft_approval_status(self, calendar_item_id: str, status: str) -> dict[str, Any]:
        self.calendar[calendar_item_id]["approval_status"] = status
        self.calendar[calendar_item_id]["draft_status"] = status
        return self.calendar[calendar_item_id]

    async def get_community_reply_draft_by_id(self, reply_draft_id: str) -> dict[str, Any] | None:
        return self.community.get(reply_draft_id)

    async def update_community_reply_approval_status(self, reply_draft_id: str, status: str) -> dict[str, Any]:
        self.community[reply_draft_id]["approval_status"] = status
        self.community[reply_draft_id]["auto_reply_allowed"] = False
        return self.community[reply_draft_id]

    async def get_report_draft_by_id(self, report_draft_id: str) -> dict[str, Any] | None:
        return self.report.get(report_draft_id)

    async def update_report_draft_approval_status(self, report_draft_id: str, status: str) -> dict[str, Any]:
        self.report[report_draft_id]["approval_status"] = status
        return self.report[report_draft_id]

    async def store_approval_audit_event(self, decision: ApprovalDecision) -> dict[str, Any]:
        event = decision.model_dump(mode="json")
        event["event_id"] = f"event-{len(self.audit_events) + 1}"
        self.audit_events.append(event)
        return event

    async def list_approval_audit_events(self, object_type: str, object_id: str) -> list[dict[str, Any]]:
        return [
            event
            for event in self.audit_events
            if event["object_type"] == object_type and event["object_id"] == object_id
        ]


def test_content_detail_dto_hides_raw_jsonb_and_includes_timeline() -> None:
    detail = content_detail_from_row(
        _content_row(),
        [
            ApprovalDecision(
                object_id="content-1",
                object_type="content_draft",
                previous_status="in_review",
                new_status="changes_requested",
                action="request_changes",
                reason="Needs one factual source.",
                requested_changes=["Add source for the performance claim."],
            )
        ],
    )
    payload = detail.model_dump(mode="json")
    serialized = json.dumps(payload)

    assert payload["caption"] == "A safe full caption for human review."
    assert payload["last_requested_changes"] == ["Add source for the performance claim."]
    assert payload["last_review_reason"] == "Needs one factual source."
    assert "content_package_json" not in serialized
    assert "quality_scores_json" not in serialized
    assert "audit_metadata_json" not in serialized


def test_detail_routes_return_safe_dtos_and_request_changes_history() -> None:
    from main import app, get_approval_service, get_persistence_repository

    repository = DetailRepository()
    app.dependency_overrides[get_persistence_repository] = lambda: repository
    app.dependency_overrides[get_approval_service] = lambda: ApprovalService(repository)  # type: ignore[arg-type]
    try:
        client = TestClient(app)
        change_response = client.post(
            "/internal/ai/approval/request-changes",
            json={
                "object_id": "content-1",
                "object_type": "content_draft",
                "reviewer_id": "reviewer-2",
                "reviewer_role": "editor",
                "reason": "The caption needs a more specific proof point.",
                "requested_changes": ["Add a proof point.", "Keep the CTA."],
            },
        )
        content = client.get("/internal/ai/approval/detail/content/content-1")
        calendar = client.get("/internal/ai/approval/detail/calendar/calendar-1")
        community = client.get("/internal/ai/approval/detail/community/reply-1")
        report = client.get("/internal/ai/approval/detail/reports/report-1")
        generic = client.get("/internal/ai/approval/detail/content_draft/content-1")

        assert change_response.status_code == 200
        assert change_response.json()["audit_event"]["requested_changes"] == ["Add a proof point.", "Keep the CTA."]
        assert content.status_code == 200
        assert content.json()["last_requested_changes"] == ["Add a proof point.", "Keep the CTA."]
        assert content.json()["latest_audit_events"][-1]["reviewer_role"] == "editor"
        assert "content_package_json" not in json.dumps(content.json())
        assert calendar.json()["content_type"] == "carousel"
        assert community.json()["auto_reply_allowed"] is False
        assert report.json()["recommendations"] == ["Review high-risk claims before reuse"]
        assert generic.status_code == 200
        assert generic.json()["object_type"] == "content_draft"
    finally:
        app.dependency_overrides.clear()


def test_detail_route_missing_invalid_and_unconfigured_responses() -> None:
    from main import app, get_approval_service, get_persistence_repository

    repository = DetailRepository()
    app.dependency_overrides[get_persistence_repository] = lambda: repository
    app.dependency_overrides[get_approval_service] = lambda: ApprovalService(repository)  # type: ignore[arg-type]
    try:
        client = TestClient(app)
        missing = client.get("/internal/ai/approval/detail/content/missing")
        invalid = client.get("/internal/ai/approval/detail/not-a-type/content-1")

        assert missing.status_code == 404
        assert missing.json()["object_type"] == "content_draft"
        assert invalid.status_code == 400
    finally:
        app.dependency_overrides.clear()

    client = TestClient(app)
    unconfigured = client.get("/internal/ai/approval/detail/content/content-1")

    assert unconfigured.status_code == 503
    assert "database pool is not configured" in unconfigured.json()["detail"]
