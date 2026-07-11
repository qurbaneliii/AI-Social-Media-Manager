from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from ai.agents import AIOrchestrator
from ai.approval.service import ApprovalService
from ai.llm import LLMClient, LLMSettings
from ai.persistence import AIPersistenceRepository


def get_ai_orchestrator(request: Request) -> AIOrchestrator:
    db_pool = getattr(request.app.state, "db_pool", None)
    persistence_repository = AIPersistenceRepository(db_pool) if db_pool is not None else None
    return AIOrchestrator(
        llm_client=LLMClient(LLMSettings()),
        persistence_repository=persistence_repository,
    )


def get_persistence_repository(request: Request) -> AIPersistenceRepository:
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="AI persistence database pool is not configured.")
    return AIPersistenceRepository(db_pool)


def get_approval_service(repository: AIPersistenceRepository = Depends(get_persistence_repository)) -> ApprovalService:
    return ApprovalService(repository)
