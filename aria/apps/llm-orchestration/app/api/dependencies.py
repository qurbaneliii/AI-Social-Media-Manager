from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ai.agents import AIOrchestrator
from ai.approval.service import ApprovalService
from ai.llm import LLMClient, LLMSettings
from ai.persistence import AIPersistenceRepository
from core.config import AppSettings, get_settings
from core.errors import APIError
from core.security import AuthenticatedPrincipal, verify_access_token
from repositories import ProductRepository


bearer_scheme = HTTPBearer(auto_error=False)


def _pool_is_usable(pool: object | None) -> bool:
    if pool is None:
        return False
    is_closing = getattr(pool, "is_closing", None)
    if callable(is_closing):
        return not bool(is_closing())
    return not bool(getattr(pool, "_closed", False))


class WorkspaceContext(BaseModel):
    workspace_id: str
    workspace_name: str
    timezone: str = "UTC"
    brand_id: str | None = None
    brand_name: str | None = None
    user_id: str
    email: str | None = None
    role: str


def get_app_settings(request: Request) -> AppSettings:
    return getattr(request.app.state, "settings", get_settings())


def get_ai_orchestrator(request: Request) -> AIOrchestrator:
    db_pool = getattr(request.app.state, "db_pool", None)
    persistence_repository = AIPersistenceRepository(db_pool) if _pool_is_usable(db_pool) else None
    return AIOrchestrator(
        llm_client=LLMClient(LLMSettings()),
        persistence_repository=persistence_repository,
    )


def get_persistence_repository(request: Request) -> AIPersistenceRepository:
    db_pool = getattr(request.app.state, "db_pool", None)
    if not _pool_is_usable(db_pool):
        raise HTTPException(status_code=503, detail="AI persistence database pool is not configured.")
    return AIPersistenceRepository(db_pool)


def get_product_repository(request: Request) -> ProductRepository:
    db_pool = getattr(request.app.state, "db_pool", None)
    if not _pool_is_usable(db_pool):
        raise APIError(503, "DATABASE_UNAVAILABLE", "The persistence database is not configured.")
    return ProductRepository(db_pool)


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: AppSettings = Depends(get_app_settings),
    test_user_id: str | None = Header(default=None, alias="X-ARIA-Test-User-ID"),
    test_email: str | None = Header(default=None, alias="X-ARIA-Test-Email"),
) -> AuthenticatedPrincipal:
    if settings.test_auth_enabled and test_user_id:
        return AuthenticatedPrincipal(user_id=test_user_id, token_subject=test_user_id, email=test_email)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError(401, "AUTHENTICATION_REQUIRED", "A valid bearer token is required.")
    return verify_access_token(credentials.credentials, settings)


async def get_workspace_context(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    repository: ProductRepository = Depends(get_product_repository),
    settings: AppSettings = Depends(get_app_settings),
    requested_workspace_id: str | None = Header(default=None, alias="X-ARIA-Workspace-ID"),
    test_role: str | None = Header(default=None, alias="X-ARIA-Test-Role"),
) -> WorkspaceContext:
    if settings.test_auth_enabled and test_role and requested_workspace_id:
        return WorkspaceContext(
            workspace_id=requested_workspace_id,
            workspace_name="Test Workspace",
            brand_id=requested_workspace_id,
            brand_name="Test Brand",
            user_id=principal.user_id,
            email=principal.email,
            role=test_role,
        )
    membership = await repository.resolve_membership(principal.user_id, requested_workspace_id)
    if membership is None:
        raise APIError(403, "WORKSPACE_ACCESS_DENIED", "The authenticated user has no access to this workspace.")
    return WorkspaceContext(
        workspace_id=str(membership["workspace_id"]),
        workspace_name=str(membership["workspace_name"]),
        timezone=str(membership.get("timezone") or "UTC"),
        brand_id=str(membership["brand_id"]) if membership.get("brand_id") else None,
        brand_name=str(membership["brand_name"]) if membership.get("brand_name") else None,
        user_id=principal.user_id,
        email=principal.email,
        role=str(membership["role"]),
    )


def require_roles(*allowed_roles: str) -> Callable[[WorkspaceContext], WorkspaceContext]:
    async def dependency(context: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if context.role not in allowed_roles:
            raise APIError(403, "INSUFFICIENT_ROLE", "The workspace role cannot perform this action.")
        return context

    return dependency


def get_approval_service(repository: AIPersistenceRepository = Depends(get_persistence_repository)) -> ApprovalService:
    return ApprovalService(repository)
