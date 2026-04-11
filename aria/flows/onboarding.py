# filename: flows/onboarding.py
# purpose: Onboarding flow orchestration for post-upload analysis, quality checks, and first test post generation.
# dependencies: asyncio, datetime, db repositories, services.brand_analysis, flows.generation

from __future__ import annotations

import asyncio
from typing import Any

import asyncpg

from db.connection import set_tenant
from db.repositories.brand_profiles import BrandProfileRepository
from db.repositories.posts import PostRepository
from services.brand_analysis import BrandAnalyzer
from flows.generation import GenerationOrchestrator


class OnboardingOrchestrator:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.brand_repo = BrandProfileRepository(pool)
        self.post_repo = PostRepository(pool)
        self.brand_analyzer = BrandAnalyzer(pool)
        self.generation = GenerationOrchestrator(pool)

    async def run_post_upload_analysis(self, company_id: str) -> dict[str, Any]:
        tone_result, visual_result = await asyncio.gather(
            self.brand_analyzer.run_tone_fingerprint(company_id),
            self.brand_analyzer.run_visual_extraction(company_id),
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await self.brand_repo.update_analysis(
                    company_id=company_id,
                    tone_fingerprint_json=tone_result,
                    visual_style_json=visual_result,
                    confidence=float(tone_result.get("tone_score", 0.0)),
                    conn=conn,
                )
        return {
            "tone_fingerprint": tone_result,
            "visual_profile": visual_result,
        }

    async def run_quality_check(self, company_id: str) -> dict[str, Any]:
        checks_total = 5
        checks_passed = 0
        remediation: list[str] = []

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                profile = await self.brand_repo.get_by_company(company_id, conn=conn)
                if profile is not None:
                    positioning_ok = bool(str(profile.get("brand_positioning_statement", "")).strip())
                    descriptors_ok = len(profile.get("tone_descriptors") or []) >= 3
                    confidence_ok = float(profile.get("confidence") or 0.0) >= 0.6
                    if positioning_ok and descriptors_ok and confidence_ok:
                        checks_passed += 1
                    else:
                        remediation.append("Complete brand profile fields and raise confidence to at least 0.6.")
                else:
                    remediation.append("Create a brand profile before running onboarding quality check.")

                staged_count = await conn.fetchval(
                    "SELECT count(*)::int FROM import_staging WHERE company_id = $1::uuid",
                    company_id,
                )
                if int(staged_count or 0) >= 10:
                    checks_passed += 1
                else:
                    remediation.append("Upload at least 10 sample posts to import staging.")

                active_credential_count = await conn.fetchval(
                    """
                    SELECT count(*)::int
                    FROM platform_credentials
                    WHERE company_id = $1::uuid
                      AND status = 'active'
                    """,
                    company_id,
                )
                if int(active_credential_count or 0) > 0:
                    checks_passed += 1
                else:
                    remediation.append("Connect at least one active platform credential.")

                expired_count = await conn.fetchval(
                    """
                    SELECT count(*)::int
                    FROM platform_credentials
                    WHERE company_id = $1::uuid
                      AND token_expires_at IS NOT NULL
                      AND token_expires_at < now()
                    """,
                    company_id,
                )
                if int(expired_count or 0) == 0:
                    checks_passed += 1
                else:
                    remediation.append("Refresh expired platform credential tokens.")

                profile_exists = profile is not None
                if profile_exists:
                    checks_passed += 1
                else:
                    remediation.append("Create the initial company and brand profile records.")

        score = float((checks_passed / checks_total) * 100.0)
        passed = score >= 70.0
        return {
            "score": score,
            "passed": passed,
            "remediation": remediation if not passed else [],
        }

    async def generate_first_test_post(self, company_id: str) -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                profile = await self.brand_repo.get_by_company(company_id, conn=conn)
                if profile is None:
                    raise ValueError("Brand profile not found")

                request = {
                    "intent": "announce",
                    "core_message": str(profile.get("brand_positioning_statement") or "Test post"),
                    "platform_targets": ["linkedin"],
                    "media_asset_id": None,
                    "campaign_tag": "onboarding-test",
                }

                post_row = await self.post_repo.create(
                    company_id=company_id,
                    intent=request["intent"],
                    core_message=request["core_message"],
                    platform_targets=request["platform_targets"],
                    created_by=None,
                    campaign_tag=request["campaign_tag"],
                    conn=conn,
                )
                post_id = str(post_row["post_id"])
                await self.post_repo.update_status(post_id, "generating", conn=conn)
        return await self.generation.run(company_id=company_id, post_id=post_id, request=request)
