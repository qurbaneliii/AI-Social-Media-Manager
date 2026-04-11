# filename: api/onboarding.py
# purpose: Onboarding API endpoints for company/profile creation, vocabulary updates, import staging, quality checks, and status.
# dependencies: uuid, fastapi, pydantic, db.connection, db.repositories, services.import_parser, flows.onboarding, app.tasks

from __future__ import annotations

from typing import Any

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException, Request
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

    company_name: str = Field(min_length=2, max_length=120)
    industry_vertical: str
    target_market: dict[str, Any]
    brand_positioning_statement: str = Field(min_length=30, max_length=500)
    tone_of_voice_descriptors: list[str] = Field(min_length=3, max_length=20)
    competitor_list: list[str] = Field(min_length=1, max_length=20)
    platform_presence: dict[str, bool]
    posting_frequency_goal: dict[str, int]
    primary_cta_types: list[str]
    brand_color_hex_codes: list[str]
    approved_vocabulary_list: list[str] = Field(default_factory=list)
    banned_vocabulary_list: list[str] = Field(default_factory=list)
    logo_file: str | None = None
    sample_post_images: list[str] = Field(default_factory=list)


class VocabularyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    approved_vocabulary_list: list[str] = Field(default_factory=list)
    banned_vocabulary_list: list[str] = Field(default_factory=list)


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    asset_id: str


class QualityCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str


@router.post("/company-profile")
async def create_company_profile(payload: CompanyProfileRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    companies = CompanyRepository(pool)
    profiles = BrandProfileRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            target_market_with_extras = {
                **payload.target_market,
                "onboarding_profile_extras": {
                    "competitor_list": payload.competitor_list,
                    "platform_presence": payload.platform_presence,
                    "posting_frequency_goal": payload.posting_frequency_goal,
                    "primary_cta_types": payload.primary_cta_types,
                    "brand_color_hex_codes": payload.brand_color_hex_codes,
                    "logo_file": payload.logo_file,
                    "sample_post_images": payload.sample_post_images,
                },
            }
            company = await companies.create(
                name=payload.company_name,
                industry_vertical=payload.industry_vertical,
                target_market=target_market_with_extras,
                timezone="UTC",
                plan_tier="standard",
                conn=conn,
            )
            company_id = str(company["company_id"])
            await set_tenant(conn, company_id)
            profile = await profiles.create(
                company_id=company_id,
                brand_positioning_statement=payload.brand_positioning_statement,
                tone_descriptors=payload.tone_of_voice_descriptors,
                tone_fingerprint_json={},
                visual_style_json=None,
                approved_vocabulary=payload.approved_vocabulary_list,
                banned_vocabulary=payload.banned_vocabulary_list,
                confidence=0.0,
                conn=conn,
            )

    return {
        "company_id": str(company["company_id"]),
        "profile_version": int(profile["profile_version"]),
        "status": "submitted",
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
                    approved=payload.approved_vocabulary_list,
                    banned=payload.banned_vocabulary_list,
                    conn=conn,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "company_id": payload.company_id,
        "approved_vocabulary_list": profile.get("approved_vocabulary", []),
        "banned_vocabulary_list": profile.get("banned_vocabulary", []),
        "status": "submitted",
    }


@router.post("/import")
async def onboarding_import(payload: ImportRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    media_service = request.app.state.media_service
    parser = ImportParser(pool)

    try:
        url = await media_service.get_asset_url(payload.asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async with httpx.AsyncClient(timeout=60.0) as client:
        file_response = await client.get(url)
        if file_response.status_code >= 400:
            raise HTTPException(status_code=400, detail="Unable to download uploaded archive")

    result = await parser.parse_and_stage(
        company_id=payload.company_id,
        file_bytes=file_response.content,
        filename=f"asset-{payload.asset_id}",
    )
    return {
        "staged_count": int(result["staged_count"]),
        "import_id": result["import_id"],
    }


@router.post("/quality-check")
async def onboarding_quality_check(payload: QualityCheckRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    orchestrator = OnboardingOrchestrator(pool)
    qc = await orchestrator.run_quality_check(payload.company_id)

    async_result = run_onboarding_quality_check.delay(payload.company_id)
    return {
        "company_id": payload.company_id,
        "score": float(qc["score"]),
        "passed": bool(qc["passed"]),
        "remediation": list(qc["remediation"]),
        "task_id": async_result.id,
    }


@router.get("/status/{company_id}")
async def onboarding_status(company_id: str, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    orchestrator = OnboardingOrchestrator(pool)

    qc = await orchestrator.run_quality_check(company_id)
    score = float(qc["score"])
    passed = bool(qc["passed"])

    if passed:
        step = 11
        status = "ready"
        remediation = None
    else:
        step = 10
        status = "remediation_required"
        remediation = qc["remediation"]

    return {
        "step": step,
        "score": score,
        "status": status,
        "remediation": remediation,
    }
