from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ai.approval import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalObjectType,
    ApprovalStatus,
    DraftNotFoundError,
    InvalidApprovalTransitionError,
)
from ai.approval.service import ApprovalService
from ai.approval.transitions import FORBIDDEN_RUNTIME_STATES, TRANSITIONS, validate_transition
from ai.persistence import AIPersistenceRepository
from ai.schemas.brand import BrandProfile
from ai.schemas.community import CommunityManagementRequest, CommunityMessageAnalysis


class InMemoryApprovalRepository:
    def __init__(self) -> None:
        self.content: dict[str, dict[str, Any]] = {
            "content-1": {"draft_id": "content-1", "approval_status": "draft"},
            "content-review": {"draft_id": "content-review", "approval_status": "in_review"},
            "content-approved": {"draft_id": "content-approved", "approval_status": "approved"},
        }
        self.calendar: dict[str, dict[str, Any]] = {
            "calendar-1": {"calendar_item_id": "calendar-1", "approval_status": "draft", "draft_status": "draft"},
            "calendar-review": {
                "calendar_item_id": "calendar-review",
                "approval_status": "in_review",
                "draft_status": "in_review",
            },
        }
        self.community: dict[str, dict[str, Any]] = {
            "reply-1": {
                "reply_draft_id": "reply-1",
                "approval_status": "draft",
                "auto_reply_allowed": False,
            },
            "reply-review": {
                "reply_draft_id": "reply-review",
                "approval_status": "in_review",
                "auto_reply_allowed": False,
            },
        }
        self.report: dict[str, dict[str, Any]] = {}
        self.audit_events: list[dict[str, Any]] = []

    async def get_content_draft_by_id(self, draft_id: str) -> dict[str, Any] | None:
        return self.content.get(draft_id)

    async def update_content_draft_approval_status(self, draft_id: str, status: str) -> dict[str, Any]:
        self.content[draft_id]["approval_status"] = status
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


class FakePersistenceConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.audit_rows: list[dict[str, Any]] = []

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        self.calls.append((query, args))
        if "UPDATE ai_content_drafts" in query:
            return {"draft_id": args[0], "approval_status": args[1], "updated_at": datetime.now(UTC)}
        if "UPDATE ai_calendar_draft_items" in query:
            return {"calendar_item_id": args[0], "approval_status": args[1], "draft_status": args[1]}
        if "UPDATE ai_community_reply_drafts" in query:
            return {"reply_draft_id": args[0], "approval_status": args[1], "auto_reply_allowed": False}
        if "INSERT INTO ai_community_reply_drafts" in query:
            return {
                "reply_draft_id": "reply-db-1",
                "brand_id": args[0],
                "approval_status": "draft",
                "auto_reply_allowed": False,
            }
        if "INSERT INTO ai_approval_audit_events" in query:
            row = {
                "event_id": "event-db-1",
                "object_id": args[0],
                "object_type": args[1],
                "previous_status": args[2],
                "new_status": args[3],
                "action": args[4],
                "reviewer_id": args[5],
                "reviewer_role": args[6],
                "reason": args[7],
                "requested_changes": args[8],
                "decision_timestamp": args[9],
                "metadata_json": args[10],
            }
            self.audit_rows.append(row)
            return row
        return None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        if "ai_approval_audit_events" in query:
            return self.audit_rows
        return []


class FakeAcquire:
    def __init__(self, conn: FakePersistenceConnection) -> None:
        self.conn = conn

    async def __aenter__(self) -> FakePersistenceConnection:
        return self.conn

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakePool:
    def __init__(self, conn: FakePersistenceConnection) -> None:
        self.conn = conn

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.conn)


def make_brand() -> BrandProfile:
    return BrandProfile(
        brand_id="brand-1",
        brand_name="ARIA Labs",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear"],
        platforms=["instagram"],
    )


def make_analysis() -> CommunityMessageAnalysis:
    return CommunityMessageAnalysis(
        message_text="Can you help me?",
        sentiment="neutral",
        intent="support_request",
        urgency="medium",
        toxicity_risk=0.0,
        crisis_risk=0.0,
        suggested_reply="Happy to help. Please send us your order details.",
        confidence=0.91,
        requires_human_review=True,
        auto_reply_allowed=False,
    )


def test_valid_content_draft_transitions() -> None:
    validate_transition(ApprovalObjectType.CONTENT_DRAFT, ApprovalStatus.DRAFT, ApprovalStatus.IN_REVIEW)
    validate_transition(ApprovalObjectType.CONTENT_DRAFT, ApprovalStatus.DRAFT, ApprovalStatus.APPROVED)
    validate_transition(ApprovalObjectType.CONTENT_DRAFT, ApprovalStatus.IN_REVIEW, ApprovalStatus.CHANGES_REQUESTED)
    validate_transition(ApprovalObjectType.CONTENT_DRAFT, ApprovalStatus.CHANGES_REQUESTED, ApprovalStatus.DRAFT)


def test_invalid_content_draft_transition() -> None:
    with pytest.raises(InvalidApprovalTransitionError):
        validate_transition(ApprovalObjectType.CONTENT_DRAFT, ApprovalStatus.APPROVED, ApprovalStatus.DRAFT)


def test_valid_and_invalid_calendar_transitions() -> None:
    validate_transition(ApprovalObjectType.CALENDAR_DRAFT, ApprovalStatus.DRAFT, ApprovalStatus.IN_REVIEW)
    validate_transition(ApprovalObjectType.CALENDAR_DRAFT, ApprovalStatus.APPROVED, ApprovalStatus.READY_FOR_SCHEDULING)

    with pytest.raises(InvalidApprovalTransitionError):
        validate_transition(ApprovalObjectType.CALENDAR_DRAFT, ApprovalStatus.DRAFT, ApprovalStatus.APPROVED)


def test_valid_and_invalid_community_reply_transitions() -> None:
    validate_transition(ApprovalObjectType.COMMUNITY_REPLY, ApprovalStatus.DRAFT, ApprovalStatus.IN_REVIEW)
    validate_transition(ApprovalObjectType.COMMUNITY_REPLY, ApprovalStatus.IN_REVIEW, ApprovalStatus.ESCALATED)

    with pytest.raises(InvalidApprovalTransitionError):
        validate_transition(ApprovalObjectType.COMMUNITY_REPLY, ApprovalStatus.APPROVED, ApprovalStatus.IN_REVIEW)


def test_no_transition_targets_published_scheduled_or_sent_states() -> None:
    assert FORBIDDEN_RUNTIME_STATES.isdisjoint({status.value for status in ApprovalStatus})
    for transition_map in TRANSITIONS.values():
        for allowed_targets in transition_map.values():
            assert FORBIDDEN_RUNTIME_STATES.isdisjoint({target.value for target in allowed_targets})


def test_approval_service_approve_reject_request_changes_archive_and_audit() -> None:
    asyncio.run(_run_service_lifecycle_check())


async def _run_service_lifecycle_check() -> None:
    repository = InMemoryApprovalRepository()
    service = ApprovalService(repository)  # type: ignore[arg-type]

    approved = await service.apply_decision(
        ApprovalDecision(
            object_id="content-1",
            object_type=ApprovalObjectType.CONTENT_DRAFT,
            new_status=ApprovalStatus.APPROVED,
            action=ApprovalAction.APPROVE,
            reason="Ready for human-approved use.",
        )
    )
    rejected = await service.apply_decision(
        ApprovalDecision(
            object_id="content-review",
            object_type=ApprovalObjectType.CONTENT_DRAFT,
            new_status=ApprovalStatus.REJECTED,
            action=ApprovalAction.REJECT,
            reason="Off-brand.",
        )
    )
    changes = await service.apply_decision(
        ApprovalDecision(
            object_id="calendar-review",
            object_type=ApprovalObjectType.CALENDAR_DRAFT,
            new_status=ApprovalStatus.CHANGES_REQUESTED,
            action=ApprovalAction.REQUEST_CHANGES,
            requested_changes=["Move date later."],
        )
    )
    archived = await service.apply_decision(
        ApprovalDecision(
            object_id="content-approved",
            object_type=ApprovalObjectType.CONTENT_DRAFT,
            new_status=ApprovalStatus.ARCHIVED,
            action=ApprovalAction.ARCHIVE,
        )
    )

    assert approved.record["approval_status"] == "approved"
    assert rejected.record["approval_status"] == "rejected"
    assert changes.record["approval_status"] == "changes_requested"
    assert archived.record["approval_status"] == "archived"
    assert len(repository.audit_events) == 4


def test_approval_service_missing_and_invalid_errors() -> None:
    asyncio.run(_run_service_error_check())


async def _run_service_error_check() -> None:
    service = ApprovalService(InMemoryApprovalRepository())  # type: ignore[arg-type]

    with pytest.raises(DraftNotFoundError):
        await service.apply_decision(
            ApprovalDecision(
                object_id="missing",
                object_type=ApprovalObjectType.CONTENT_DRAFT,
                new_status=ApprovalStatus.APPROVED,
                action=ApprovalAction.APPROVE,
            )
        )

    with pytest.raises(InvalidApprovalTransitionError):
        await service.apply_decision(
            ApprovalDecision(
                object_id="calendar-1",
                object_type=ApprovalObjectType.CALENDAR_DRAFT,
                new_status=ApprovalStatus.APPROVED,
                action=ApprovalAction.APPROVE,
            )
        )


def test_repository_phase_4_methods_update_statuses_and_audit_events() -> None:
    asyncio.run(_run_repository_phase_4_check())


async def _run_repository_phase_4_check() -> None:
    conn = FakePersistenceConnection()
    repository = AIPersistenceRepository(FakePool(conn))

    content = await repository.update_content_draft_approval_status("content-db-1", "approved")
    calendar = await repository.update_calendar_draft_approval_status("calendar-db-1", "ready_for_scheduling")
    community = await repository.update_community_reply_approval_status("reply-db-1", "approved")
    event = await repository.store_approval_audit_event(
        ApprovalDecision(
            object_id="content-db-1",
            object_type=ApprovalObjectType.CONTENT_DRAFT,
            previous_status=ApprovalStatus.DRAFT,
            new_status=ApprovalStatus.APPROVED,
            action=ApprovalAction.APPROVE,
            reason="Approved in test.",
        )
    )
    listed = await repository.list_approval_audit_events("content_draft", "content-db-1")

    assert content["approval_status"] == "approved"
    assert calendar["approval_status"] == "ready_for_scheduling"
    assert community["auto_reply_allowed"] is False
    assert event["new_status"] == "approved"
    assert listed[0]["action"] == "approve"


def test_repository_stores_community_reply_draft_as_non_auto_reply() -> None:
    asyncio.run(_run_repository_community_draft_check())


async def _run_repository_community_draft_check() -> None:
    repository = AIPersistenceRepository(FakePool(FakePersistenceConnection()))
    saved = await repository.save_community_reply_draft(
        brand_id="brand-1",
        analysis=make_analysis(),
        metadata={"source": "test"},
    )

    assert saved["approval_status"] == "draft"
    assert saved["auto_reply_allowed"] is False


def test_phase_4_routes_are_registered() -> None:
    from main import app

    paths = {route.path for route in app.routes}
    assert {
        "/internal/ai/approval/decision",
        "/internal/ai/approval/submit",
        "/internal/ai/approval/approve",
        "/internal/ai/approval/reject",
        "/internal/ai/approval/request-changes",
        "/internal/ai/approval/archive",
        "/internal/ai/approval/audit/{object_type}/{object_id}",
        "/internal/ai/drafts/content",
        "/internal/ai/drafts/calendar",
        "/internal/ai/drafts/community",
    }.issubset(paths)


def test_approval_decision_route_response_and_invalid_transition() -> None:
    from main import app, get_approval_service

    repository = InMemoryApprovalRepository()
    app.dependency_overrides[get_approval_service] = lambda: ApprovalService(repository)  # type: ignore[arg-type]
    try:
        client = TestClient(app)
        response = client.post(
            "/internal/ai/approval/approve",
            json={
                "object_id": "content-1",
                "object_type": "content_draft",
                "reviewer_id": "reviewer-1",
                "reason": "Good to use internally.",
            },
        )
        invalid = client.post(
            "/internal/ai/approval/approve",
            json={
                "object_id": "content-1",
                "object_type": "content_draft",
                "reason": "Cannot approve twice.",
            },
        )
        audit = client.get("/internal/ai/approval/audit/content_draft/content-1")

        assert response.status_code == 200
        assert response.json()["decision"]["new_status"] == "approved"
        assert response.json()["record"]["approval_status"] == "approved"
        assert invalid.status_code == 409
        assert audit.status_code == 200
        assert audit.json()[0]["action"] == "approve"
    finally:
        app.dependency_overrides.clear()


def test_approval_route_missing_object_response() -> None:
    from main import app, get_approval_service

    app.dependency_overrides[get_approval_service] = lambda: ApprovalService(InMemoryApprovalRepository())  # type: ignore[arg-type]
    try:
        client = TestClient(app)
        response = client.post(
            "/internal/ai/approval/approve",
            json={"object_id": "missing", "object_type": "content_draft"},
        )

        assert response.status_code == 404
        assert response.json()["object_id"] == "missing"
    finally:
        app.dependency_overrides.clear()


def test_draft_listing_route_response_shape() -> None:
    from main import app, get_persistence_repository

    class ListRepository:
        async def list_content_drafts(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            return [
                {
                    "draft_id": "content-1",
                    "brand_id": kwargs.get("brand_id"),
                    "platform": "linkedin",
                    "content_type": "post",
                    "topic": "approval",
                    "content_package_json": {"hook": "Hook", "caption": "Caption", "posting_recommendation": {"approval_required": True}},
                    "quality_scores_json": {"approval_status": "requires_human_review"},
                    "approval_status": kwargs.get("status") or "draft",
                    "model": "gpt-4o-mini",
                    "mock_mode": True,
                }
            ]

    app.dependency_overrides[get_persistence_repository] = lambda: ListRepository()
    try:
        client = TestClient(app)
        response = client.get("/internal/ai/drafts/content?brand_id=brand-1&status=draft")

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["items"][0]["approval_status"] == "draft"
    finally:
        app.dependency_overrides.clear()


def test_community_analysis_route_persists_draft_without_auto_reply() -> None:
    from main import app, get_ai_orchestrator

    class CommunityPersistence:
        def __init__(self) -> None:
            self.saved: list[dict[str, Any]] = []

        async def save_community_reply_draft(
            self,
            *,
            brand_id: str,
            analysis: CommunityMessageAnalysis,
            metadata: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            self.saved.append(
                {
                    "brand_id": brand_id,
                    "analysis": analysis,
                    "metadata": metadata or {},
                    "auto_reply_allowed": False,
                }
            )
            return {"reply_draft_id": "reply-1", "auto_reply_allowed": False}

    class CommunityOrchestrator:
        def __init__(self) -> None:
            self.persistence_repository = CommunityPersistence()

        async def analyze_community_message(self, request: CommunityManagementRequest) -> CommunityMessageAnalysis:
            return make_analysis()

    fake_orchestrator = CommunityOrchestrator()
    app.dependency_overrides[get_ai_orchestrator] = lambda: fake_orchestrator
    try:
        client = TestClient(app)
        response = client.post(
            "/internal/ai/community/analyze",
            json={
                "brand_profile": make_brand().model_dump(mode="json"),
                "platform": "instagram",
                "message_text": "Can you help me?",
            },
        )

        assert response.status_code == 200
        assert response.json()["auto_reply_allowed"] is False
        assert fake_orchestrator.persistence_repository.saved[0]["auto_reply_allowed"] is False
    finally:
        app.dependency_overrides.clear()


def test_ai_approval_lifecycle_migration_sql_shape() -> None:
    migration = Path("aria/db/migrations/008_ai_approval_lifecycle.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS ai_community_reply_drafts" in migration
    assert "CREATE TABLE IF NOT EXISTS ai_approval_audit_events" in migration
    assert "CREATE TABLE IF NOT EXISTS ai_report_drafts" in migration
    assert "auto_reply_allowed BOOLEAN NOT NULL DEFAULT false CHECK (auto_reply_allowed = false)" in migration
    assert "ready_for_scheduling" in migration
    assert "JSONB NOT NULL DEFAULT '{}'::jsonb" in migration
    assert "idx_ai_approval_audit_events_object_created" in migration
    assert "'published'" not in migration
    assert "'sent'" not in migration
    assert "'scheduled'" not in migration
