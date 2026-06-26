from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.approval.queue import content_queue_item_from_row


def _content_row() -> dict[str, Any]:
    return {
        "draft_id": "content-1",
        "brand_id": "brand-1",
        "platform": "linkedin",
        "content_type": "post",
        "topic": "approval lifecycle",
        "content_package_json": {
            "hook": "A useful hook for the approval queue.",
            "caption": "A caption that is safe to preview.",
            "risks": ["Needs fact check"],
            "posting_recommendation": {"approval_required": True},
        },
        "quality_scores_json": {
            "brand_consistency_score": 0.9,
            "platform_fit_score": 0.86,
            "clarity_score": 0.88,
            "approval_status": "requires_human_review",
        },
        "approval_status": "draft",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "model": "gpt-4o-mini",
        "mock_mode": True,
    }


def _calendar_row() -> dict[str, Any]:
    return {
        "calendar_item_id": "calendar-1",
        "brand_id": "brand-1",
        "platform": "linkedin",
        "scheduled_date": "2026-06-20",
        "scheduled_time": "09:30:00",
        "approval_status": "draft",
        "draft_status": "draft",
        "calendar_item_json": {
            "content_pillar": "authority",
            "objective": "educate",
            "topic": "approval queues",
        },
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


def _community_row() -> dict[str, Any]:
    return {
        "reply_draft_id": "reply-1",
        "brand_id": "brand-1",
        "original_message_text": "Can you help me with this order?",
        "suggested_reply": "Absolutely. Please send your order details so we can check.",
        "sentiment": "neutral",
        "intent": "support_request",
        "urgency": "medium",
        "toxicity_risk": 0.0,
        "crisis_risk": 0.0,
        "requires_human_review": True,
        "escalation_reason": None,
        "auto_reply_allowed": False,
        "approval_status": "draft",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


def _report_row() -> dict[str, Any]:
    return {
        "report_draft_id": "report-1",
        "brand_id": "brand-1",
        "report_type": "weekly",
        "date_range": "2026-06-01..2026-06-07",
        "insight_payload_json": {"summary": "Weekly performance improved across approval-safe posts."},
        "approval_status": "draft",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


class QueueRepository:
    async def list_content_drafts(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [_content_row()]

    async def list_calendar_drafts(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [_calendar_row()]

    async def list_community_reply_drafts(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [_community_row()]

    async def list_report_drafts(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [_report_row()]


def test_content_queue_dto_hides_raw_json_blobs() -> None:
    item = content_queue_item_from_row(_content_row())
    payload = item.model_dump(mode="json")

    assert payload["draft_id"] == "content-1"
    assert payload["hook_preview"].startswith("A useful hook")
    assert payload["requires_human_review"] is True
    assert "content_package_json" not in payload
    assert "quality_scores_json" not in payload


def test_approval_queue_routes_return_stable_dtos() -> None:
    from main import app, get_persistence_repository

    app.dependency_overrides[get_persistence_repository] = lambda: QueueRepository()
    try:
        client = TestClient(app)
        content = client.get("/internal/ai/approval/queue/content?brand_id=brand-1&status=draft")
        calendar = client.get("/internal/ai/approval/queue/calendar?brand_id=brand-1")
        community = client.get("/internal/ai/approval/queue/community?brand_id=brand-1")
        reports = client.get("/internal/ai/approval/queue/reports?brand_id=brand-1")
        aggregate = client.get("/internal/ai/approval/queue?brand_id=brand-1")

        assert content.status_code == 200
        assert content.json()["items"][0]["caption_preview"] == "A caption that is safe to preview."
        assert "content_package_json" not in content.json()["items"][0]
        assert calendar.json()["items"][0]["readiness_status"] == "draft"
        assert community.json()["items"][0]["auto_reply_allowed"] is False
        assert reports.json()["items"][0]["summary_preview"].startswith("Weekly performance")
        assert aggregate.status_code == 200
        assert aggregate.json()["count"] == 4
    finally:
        app.dependency_overrides.clear()


def test_approval_queue_invalid_filter_returns_400() -> None:
    from main import app, get_persistence_repository

    app.dependency_overrides[get_persistence_repository] = lambda: QueueRepository()
    try:
        client = TestClient(app)
        response = client.get("/internal/ai/approval/queue/calendar?status=escalated")

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_approval_queue_returns_503_when_persistence_missing() -> None:
    from main import app

    client = TestClient(app)
    response = client.get("/internal/ai/approval/queue/content")

    assert response.status_code == 503
    assert "database pool is not configured" in response.json()["detail"]


def test_lifespan_creates_db_pool_when_database_url_is_configured(monkeypatch: Any) -> None:
    asyncio.run(_run_lifespan_pool_check(monkeypatch))


async def _run_lifespan_pool_check(monkeypatch: Any) -> None:
    from main import get_ai_orchestrator, lifespan

    class FakePool:
        async def close(self) -> None:
            self.closed = True

    async def create_pool(url: str, min_size: int, max_size: int) -> FakePool:
        assert url == "postgresql://test:test@localhost:5432/test"
        assert min_size == 1
        assert max_size == 5
        return FakePool()

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setitem(sys.modules, "asyncpg", SimpleNamespace(create_pool=create_pool))
    fake_app = FastAPI()

    async with lifespan(fake_app):
        assert fake_app.state.db_pool is not None
        request = SimpleNamespace(app=fake_app)
        orchestrator = get_ai_orchestrator(request)
        assert orchestrator.persistence_repository is not None
