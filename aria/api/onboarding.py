# filename: api/onboarding.py
# purpose: Onboarding API endpoints for company/profile creation, vocabulary updates, import staging, quality checks, and status.
# dependencies: uuid, fastapi, pydantic, db.connection, db.repositories, services.import_parser, flows.onboarding, app.tasks

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.tasks import run_onboarding_quality_check
from db.connection import set_tenant
from db.repositories.brand_profiles import BrandProfileRepository
from db.repositories.companies import CompanyRepository
from flows.onboarding import OnboardingOrchestrator
from services.import_parser import ImportParser

router = APIRouter()

SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class CompanyProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    industry_vertical: str
    target_market: dict[str, Any]
    timezone: str = "UTC"
    plan_tier: str
    brand_positioning_statement: str
    tone_descriptors: list[str]


class VocabularyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    approved: list[str] = Field(default_factory=list)
    banned: list[str] = Field(default_factory=list)


@router.post("/company-profile")
async def create_company_profile(payload: CompanyProfileRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    companies = CompanyRepository(pool)
    profiles = BrandProfileRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            company = await companies.create(
                name=payload.name,
                industry_vertical=payload.industry_vertical,
                target_market=payload.target_market,
                timezone=payload.timezone,
                plan_tier=payload.plan_tier,
                conn=conn,
            )
            company_id = str(company["company_id"])
            await set_tenant(conn, company_id)
            profile = await profiles.create(
                company_id=company_id,
                brand_positioning_statement=payload.brand_positioning_statement,
                tone_descriptors=payload.tone_descriptors,
                tone_fingerprint_json={},
                visual_style_json=None,
                confidence=0.0,
                conn=conn,
            )

    return {
        "company_id": str(company["company_id"]),
        "profile_id": str(profile["profile_id"]),
        "status": "draft",
    }


@router.post("/vocabulary")
async def update_vocabulary(payload: VocabularyRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    repo = BrandProfileRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, payload.company_id)
            try:
                profile = await repo.update_vocabulary(
                    company_id=payload.company_id,
                    approved=payload.approved,
                    banned=payload.banned,
                    conn=conn,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
    return profile


@router.post("/import")
async def onboarding_import(
    request: Request,
    company_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    parser = ImportParser(pool)
    content = await file.read()
    result = await parser.parse_and_stage(company_id=company_id, file_bytes=content, filename=file.filename or "")
    return {
        "staged_count": int(result["staged_count"]),
        "import_id": result["import_id"],
    }


@router.post("/quality-check")
async def onboarding_quality_check(company_id: str) -> dict[str, str]:
    async_result = run_onboarding_quality_check.delay(company_id)
    return {"task_id": async_result.id}


@router.get("/status/{company_id}")
async def onboarding_status(company_id: str, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    orchestrator = OnboardingOrchestrator(pool)

    qc = await orchestrator.run_quality_check(company_id)
    score = float(qc["score"])
    passed = bool(qc["passed"])

    if passed:
        step = 5
        status = "ready"
        remediation = None
    else:
        step = 4
        status = "remediation_required"
        remediation = qc["remediation"]

    return {
        "step": step,
        "score": score,
        "status": status,
        "remediation": remediation,
    }
