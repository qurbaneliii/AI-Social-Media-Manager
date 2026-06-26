from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from ai.agents import AIOrchestrator
from ai.llm import LLMClient, LLMSettings
from ai.memory import BrandMemory, BrandProfileNotFoundError
from ai.persistence import AIPersistenceRepository, PersistenceAuditMetadata
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest
from ai.schemas.content import ContentRequest, PlatformContext


def make_brand() -> BrandProfile:
    return BrandProfile(
        brand_id="brand-1",
        brand_name="ARIA Labs",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
        platforms=["linkedin"],
    )


def make_client() -> LLMClient:
    return LLMClient(
        LLMSettings(
            OPENAI_API_KEY=None,
            AI_MOCK_MODE=True,
            OPENAI_MODEL="gpt-4o-mini",
            AI_TEMPERATURE=0.4,
        )
    )


class FakeAcquire:
    def __init__(self, conn: "FakeConnection") -> None:
        self.conn = conn

    async def __aenter__(self) -> "FakeConnection":
        return self.conn

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakePool:
    def __init__(self, conn: "FakeConnection") -> None:
        self.conn = conn

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.conn)


class FakeConnection:
    def __init__(self, stored_brand: BrandProfile | None = None) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.brand = stored_brand

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any]:
        self.calls.append((query, args))
        if "SELECT brand_profile_json" in query:
            return {"brand_profile_json": self.brand.model_dump(mode="json")} if self.brand is not None else None
        if "ai_content_drafts" in query:
            return {"draft_id": "00000000-0000-0000-0000-000000000001", "approval_status": args[5]}
        if "ai_quality_reviews" in query:
            return {"review_id": "00000000-0000-0000-0000-000000000002", "approval_status": args[2]}
        if "ai_calendar_draft_items" in query:
            return {"calendar_item_id": "00000000-0000-0000-0000-000000000003", "draft_status": args[4]}
        return {"brand_id": args[0]}


def test_ai_persistence_repository_loads_saved_brand_profile() -> None:
    asyncio.run(_run_repository_brand_profile_check())


async def _run_repository_brand_profile_check() -> None:
    conn = FakeConnection(stored_brand=make_brand())
    repository = AIPersistenceRepository(FakePool(conn))

    loaded = await repository.load_brand_profile("brand-1")
    await repository.save_brand_profile(make_brand())

    assert loaded is not None
    assert loaded.brand_name == "ARIA Labs"
    assert any("ai_brand_memory" in query for query, _ in conn.calls)


def test_brand_memory_loads_stored_profile_before_agents() -> None:
    asyncio.run(_run_brand_memory_stored_profile_check())


async def _run_brand_memory_stored_profile_check() -> None:
    stored = make_brand().model_copy(update={"brand_name": "Stored ARIA"})
    repository = AIPersistenceRepository(FakePool(FakeConnection(stored_brand=stored)))
    memory = BrandMemory(repository, allow_profile_bootstrap=False)

    loaded = await memory.load_brand_profile(make_brand())

    assert loaded.brand_name == "Stored ARIA"


def test_brand_memory_missing_profile_raises_in_real_repository_mode() -> None:
    asyncio.run(_run_brand_memory_missing_profile_check())


async def _run_brand_memory_missing_profile_check() -> None:
    repository = AIPersistenceRepository(FakePool(FakeConnection(stored_brand=None)))
    memory = BrandMemory(repository, allow_profile_bootstrap=False)

    with pytest.raises(BrandProfileNotFoundError):
        await memory.load_brand_profile(make_brand())


def test_orchestrator_persists_content_drafts_reviews_and_calendar_items() -> None:
    asyncio.run(_run_orchestrator_persistence_check())


async def _run_orchestrator_persistence_check() -> None:
    conn = FakeConnection(stored_brand=make_brand())
    repository = AIPersistenceRepository(FakePool(conn))
    orchestrator = AIOrchestrator(llm_client=make_client(), persistence_repository=repository)
    brand = make_brand()
    platform = PlatformContext(platform="linkedin", content_type="post", objective="educate", hashtag_limit=3)

    package = await orchestrator.generate_content_package(
        ContentRequest(
            brand_profile=brand,
            platform_context=platform,
            campaign_objective="build trust",
            topic="approval-based AI",
            content_pillar="authority",
        )
    )
    calendar = await orchestrator.create_content_calendar(
        CalendarPlanningRequest(
            brand_profile=brand,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 22),
            platforms=["linkedin"],
        )
    )

    queries = "\n".join(query for query, _ in conn.calls)
    assert package.quality_scores is not None
    assert package.quality_scores.approval_status == "requires_human_review"
    assert calendar.approval_required is True
    assert "INSERT INTO ai_content_drafts" in queries
    assert "INSERT INTO ai_quality_reviews" in queries
    assert "INSERT INTO ai_calendar_draft_items" in queries
    assert any(args[-1] is True for query, args in conn.calls if "ai_content_drafts" in query)


def test_runtime_dependency_pattern_builds_persistent_orchestrator_when_pool_exists() -> None:
    from main import get_ai_orchestrator

    fake_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_pool=FakePool(FakeConnection()))))
    orchestrator = get_ai_orchestrator(fake_request)

    assert orchestrator.persistence_repository is not None


def test_persistence_audit_metadata_records_model_mock_mode_and_prompt_version() -> None:
    metadata = PersistenceAuditMetadata(model="gpt-4o-mini", mock_mode=True, prompt_version="v1")

    assert metadata.model == "gpt-4o-mini"
    assert metadata.mock_mode is True
    assert metadata.prompt_version == "v1"
    assert metadata.generated_at.tzinfo is not None


def test_internal_phase_2_routes_are_registered() -> None:
    from main import app

    paths = {route.path for route in app.routes}
    assert {
        "/internal/ai/generate-content-package",
        "/internal/ai/brand-strategy",
        "/internal/ai/competitors/analyze",
        "/internal/ai/trends/research",
        "/internal/ai/hashtags/recommend",
        "/internal/ai/visual-concept",
        "/internal/ai/content-calendar",
        "/internal/ai/community/analyze",
        "/internal/ai/reports/insights",
        "/internal/ai/content-quality/review",
    }.issubset(paths)


def test_internal_routes_return_schema_shaped_mock_responses_without_publish_or_reply() -> None:
    from main import app

    brand = make_brand().model_dump(mode="json")
    client = TestClient(app)

    content_response = client.post(
        "/internal/ai/generate-content-package",
        json={
            "brand_profile": brand,
            "platform_context": {"platform": "linkedin", "content_type": "post", "objective": "educate"},
            "campaign_objective": "build trust",
            "topic": "approval-based AI",
            "content_pillar": "authority",
        },
    )
    community_response = client.post(
        "/internal/ai/community/analyze",
        json={
            "brand_profile": brand,
            "platform": "instagram",
            "message_text": "Can I get a refund urgently?",
        },
    )

    assert content_response.status_code == 200
    assert content_response.json()["quality_scores"]["approval_status"] == "requires_human_review"
    assert content_response.json()["posting_recommendation"]["approval_required"] is True
    assert community_response.status_code == 200
    assert community_response.json()["requires_human_review"] is True
    assert community_response.json()["auto_reply_allowed"] is False


def test_ai_memory_migration_sql_shape_matches_repo_conventions() -> None:
    migration = Path("aria/db/migrations/007_ai_memory_foundation.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS ai_brand_memory" in migration
    assert "CREATE TABLE IF NOT EXISTS ai_content_drafts" in migration
    assert "CREATE TABLE IF NOT EXISTS ai_quality_reviews" in migration
    assert "CREATE TABLE IF NOT EXISTS ai_calendar_draft_items" in migration
    assert "JSONB NOT NULL" in migration
    assert "TIMESTAMPTZ NOT NULL DEFAULT now()" in migration
    assert "approval_status" in migration
    assert "requires_human_review" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_ai_content_drafts_brand_created" in migration
    assert "REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE" in migration
