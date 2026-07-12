from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_workspace_context
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
