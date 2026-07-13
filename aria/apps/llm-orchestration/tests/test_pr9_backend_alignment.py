from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_workspace_context
from api.dependencies import WorkspaceContext, get_product_repository
from core.config import AppSettings
from core.errors import APIError, register_error_handlers
from core.security import AuthenticatedPrincipal, verify_access_token


SECRET = "test-secret-that-is-long-enough-for-contract-tests"


def _token(**overrides: object) -> str:
    now = datetime.now(tz=UTC)
    claims = {
        "sub": "user-1",
        "userId": "user-1",
        "email": "user@example.com",
        "iss": "aria-frontend",
        "aud": "aria-api",
        "iat": now,
        "exp": now + timedelta(minutes=10),
        **overrides,
    }
    return jwt.encode(claims, SECRET, algorithm="HS256")


def _settings() -> AppSettings:
    return AppSettings(JWT_SECRET=SECRET, ARIA_ENV="production")


def test_access_token_requires_matching_issuer_audience_and_subject() -> None:
    principal = verify_access_token(_token(), _settings())
    assert principal.user_id == "user-1"
    assert principal.email == "user@example.com"

    with pytest.raises(APIError) as issuer_error:
        verify_access_token(_token(iss="untrusted"), _settings())
    assert issuer_error.value.code == "INVALID_ACCESS_TOKEN"

    with pytest.raises(APIError) as audience_error:
        verify_access_token(_token(aud="other-api"), _settings())
    assert audience_error.value.code == "INVALID_ACCESS_TOKEN"


class MembershipRepository:
    def __init__(self, membership: dict | None) -> None:
        self.membership = membership
        self.requested: tuple[str, str | None] | None = None

    async def resolve_membership(self, user_id: str, workspace_id: str | None) -> dict | None:
        self.requested = (user_id, workspace_id)
        return self.membership


def test_workspace_role_is_derived_from_membership_not_token_metadata() -> None:
    repository = MembershipRepository(
        {
            "workspace_id": "workspace-1",
            "workspace_name": "Workspace",
            "timezone": "Asia/Baku",
            "brand_id": "brand-1",
            "brand_name": "Brand",
            "role": "analyst",
        }
    )
    context = asyncio.run(
        get_workspace_context(
            principal=AuthenticatedPrincipal(user_id="user-1", token_subject="user-1", email="user@example.com"),
            repository=repository,
            settings=_settings(),
            requested_workspace_id="workspace-1",
            test_role="agency_admin",
        )
    )
    assert context.role == "analyst"
    assert repository.requested == ("user-1", "workspace-1")


def test_workspace_access_denied_when_membership_is_missing() -> None:
    with pytest.raises(APIError) as denied:
        asyncio.run(
            get_workspace_context(
                principal=AuthenticatedPrincipal(user_id="user-1", token_subject="user-1"),
                repository=MembershipRepository(None),
                settings=_settings(),
                requested_workspace_id="workspace-2",
                test_role=None,
            )
        )
    assert denied.value.status_code == 403
    assert denied.value.code == "WORKSPACE_ACCESS_DENIED"


def test_structured_api_error_does_not_expose_internal_exception_text() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/protected")
    async def protected() -> None:
        raise APIError(403, "DENIED", "Access denied.")

    response = TestClient(app).get("/protected")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DENIED"
    assert "traceback" not in response.text.lower()


def test_canonical_product_routes_are_registered() -> None:
    from main import app

    route_contract = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    expected = {
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
        ("GET", "/health/dependencies"),
        ("GET", "/v1/session"),
        ("GET", "/v1/brands/{brand_id}/profile"),
        ("PUT", "/v1/brands/{brand_id}/profile"),
        ("GET", "/v1/content"),
        ("GET", "/v1/calendar/items"),
        ("GET", "/v1/calendar/unscheduled"),
        ("GET", "/v1/overview"),
        ("GET", "/v1/insights"),
        ("GET", "/v1/capabilities"),
        ("GET", "/v1/audit"),
        ("GET", "/v1/approval/queue"),
        ("GET", "/v1/approval/detail/{object_type}/{object_id}"),
        ("POST", "/v1/approval/decision"),
    }
    assert expected.issubset(route_contract)


def test_alignment_migration_adds_tenant_keys_and_revokes_direct_data_api_access() -> None:
    migration = Path(__file__).resolve().parents[3] / "db" / "migrations" / "010_pr9_backend_alignment.sql"
    sql = migration.read_text(encoding="utf-8").lower()
    assert "create table if not exists ai_workspaces" in sql
    assert "create table if not exists ai_workspace_memberships" in sql
    assert "create table if not exists ai_content_variants" in sql
    assert "alter table ai_content_drafts add column if not exists workspace_id" in sql
    assert "revoke all on table" in sql
    assert "from anon, authenticated" in sql
    assert "alter table ai_community_reply_drafts add column if not exists workspace_id" in sql
    assert "alter table ai_report_drafts add column if not exists workspace_id" in sql


class ApprovalContractRepository:
    def __init__(self) -> None:
        self.decision: dict | None = None

    async def list_approval_queue(self, **values: object) -> tuple[list[dict], int]:
        return (
            [
                {
                    "object_type": "content_draft",
                    "payload": {
                        "draft_id": "00000000-0000-0000-0000-000000000001",
                        "brand_id": "brand-1",
                        "platform": "linkedin",
                        "content_type": "post",
                        "topic": "Tenant-safe approvals",
                        "content_package_json": {"hook": "Review this", "caption": "Approval draft"},
                        "approval_status": "in_review",
                        "quality_scores_json": {},
                        "audit_metadata_json": {},
                        "created_at": datetime.now(tz=UTC),
                    },
                }
            ],
            47,
        )

    async def apply_approval_decision(self, **values: object) -> dict:
        self.decision = values
        return {
            "record": {"draft_id": values["object_id"], "approval_status": "approved"},
            "event": {
                "event_id": "00000000-0000-0000-0000-000000000099",
                "object_id": values["object_id"],
                "object_type": values["object_type"],
                "previous_status": "in_review",
                "new_status": values["new_status"],
                "action": values["action"],
                "reviewer_id": values["actor_user_id"],
                "reviewer_role": values["actor_role"],
                "reason": values["reason"],
                "requested_changes": values["requested_changes"],
                "timestamp": datetime.now(tz=UTC),
                "metadata": values["metadata"],
            },
        }


def test_approval_queue_uses_global_total_and_decision_uses_trusted_actor() -> None:
    from main import app

    repository = ApprovalContractRepository()
    app.dependency_overrides[get_product_repository] = lambda: repository
    app.dependency_overrides[get_workspace_context] = lambda: WorkspaceContext(
        workspace_id="workspace-1",
        workspace_name="Workspace",
        brand_id="brand-1",
        brand_name="Brand",
        user_id="trusted-user",
        email="trusted@example.com",
        role="brand_manager",
    )
    client = TestClient(app)
    queue = client.get("/v1/approval/queue?limit=1&offset=0")
    assert queue.status_code == 200
    assert queue.json()["count"] == 47
    assert len(queue.json()["items"]) == 1

    decision = client.post(
        "/v1/approval/approve",
        json={
            "object_id": "00000000-0000-0000-0000-000000000001",
            "object_type": "content_draft",
            "reviewer_id": "attacker-controlled",
            "reviewer_role": "agency_admin",
            "reason": "Reviewed",
        },
    )
    assert decision.status_code == 200
    assert repository.decision is not None
    assert repository.decision["actor_user_id"] == "trusted-user"
    assert repository.decision["actor_role"] == "brand_manager"
    assert decision.json()["decision"]["reviewer_id"] == "trusted-user"
    app.dependency_overrides.clear()


def test_legacy_approval_and_run_routes_are_retired_in_production() -> None:
    from main import app

    with TestClient(app) as client:
        previous = app.state.settings
        app.state.settings = AppSettings(ARIA_ENV="production", JWT_SECRET=SECRET)
        approval = client.get("/internal/ai/approval/queue")
        run = client.post("/run", json={})
        app.state.settings = previous
    assert approval.status_code == 410
    assert approval.json()["error"]["code"] == "LEGACY_ROUTE_RETIRED"
    assert run.status_code == 410
