from __future__ import annotations

import asyncio
import os
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest

from ai.agents import AIOrchestrator
from ai.llm import LLMClient, LLMSettings
from ai.memory import BrandMemory
from ai.persistence import AIPersistenceRepository
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest
from ai.schemas.content import ContentRequest, PlatformContext


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_DB_TESTS") != "1" or not os.getenv("DATABASE_URL"),
    reason="Phase 3.5 live Postgres tests require RUN_LIVE_DB_TESTS=1 and DATABASE_URL.",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _make_brand() -> BrandProfile:
    suffix = uuid4().hex[:8]
    return BrandProfile(
        brand_id=f"phase35-{suffix}",
        brand_name=f"Phase 3.5 Brand {suffix}",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
        platforms=["linkedin"],
    )


def test_phase_3_5_live_database_persistence_flow() -> None:
    asyncio.run(_run_live_database_persistence_flow())


async def _run_live_database_persistence_flow() -> None:
    import asyncpg

    repo_root = _repo_root()
    aria_root = repo_root / "aria"
    sys.path.insert(0, str(aria_root))
    from db.migrate import run_migrations

    await run_migrations()

    brand = _make_brand()
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    try:
        repository = AIPersistenceRepository(pool)
        await repository.save_brand_profile(brand)

        memory = BrandMemory(repository, allow_profile_bootstrap=False)
        loaded = await memory.load_brand_profile(brand)
        assert loaded.brand_id == brand.brand_id
        assert loaded.brand_name == brand.brand_name

        orchestrator = AIOrchestrator(
            llm_client=LLMClient(
                LLMSettings(
                    OPENAI_API_KEY=None,
                    AI_MOCK_MODE=True,
                    OPENAI_MODEL="gpt-4o-mini",
                    AI_TEMPERATURE=0.4,
                )
            ),
            brand_memory=memory,
            persistence_repository=repository,
        )
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

        async with pool.acquire() as conn:
            draft_count = await conn.fetchval("SELECT count(*) FROM ai_content_drafts WHERE brand_id = $1", brand.brand_id)
            review_count = await conn.fetchval("SELECT count(*) FROM ai_quality_reviews WHERE brand_id = $1", brand.brand_id)
            calendar_count = await conn.fetchval(
                "SELECT count(*) FROM ai_calendar_draft_items WHERE brand_id = $1",
                brand.brand_id,
            )
            table_names = await conn.fetch(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename = ANY($1::text[])
                """,
                ["ai_brand_memory", "ai_content_drafts", "ai_quality_reviews", "ai_calendar_draft_items"],
            )

        assert {row["tablename"] for row in table_names} == {
            "ai_brand_memory",
            "ai_content_drafts",
            "ai_quality_reviews",
            "ai_calendar_draft_items",
        }
        assert package.quality_scores is not None
        assert package.quality_scores.approval_status == "requires_human_review"
        assert calendar.approval_required is True
        assert draft_count >= 1
        assert review_count >= 1
        assert calendar_count >= len(calendar.items)
    finally:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM ai_brand_memory WHERE brand_id = $1", brand.brand_id)
        await pool.close()
