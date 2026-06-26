from __future__ import annotations

import asyncio
import os
from datetime import date
from uuid import uuid4

import pytest

from ai.agents import AIOrchestrator
from ai.approval import ApprovalAction, ApprovalDecision, ApprovalObjectType, ApprovalStatus
from ai.approval.service import ApprovalService
from ai.llm import LLMClient, LLMSettings
from ai.memory import BrandMemory
from ai.persistence import AIPersistenceRepository
from ai.schemas.analytics import ReportingInsightRequest
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import CalendarPlanningRequest
from ai.schemas.community import CommunityManagementRequest
from ai.schemas.content import ContentRequest, PlatformContext


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_DB_TESTS") != "1" or not os.getenv("DATABASE_URL"),
    reason="Phase 5 live Postgres tests require RUN_LIVE_DB_TESTS=1 and DATABASE_URL.",
)


def _make_brand() -> BrandProfile:
    suffix = uuid4().hex[:8]
    return BrandProfile(
        brand_id=f"phase5-{suffix}",
        brand_name=f"Phase 5 Brand {suffix}",
        industry="Marketing software",
        target_audience=["founders"],
        tone_of_voice=["clear", "useful"],
        platforms=["linkedin", "instagram"],
    )


def test_phase_5_live_database_approval_flow() -> None:
    asyncio.run(_run_phase_5_live_flow())


async def _run_phase_5_live_flow() -> None:
    import asyncpg

    required_tables = {
        "ai_brand_memory",
        "ai_content_drafts",
        "ai_quality_reviews",
        "ai_calendar_draft_items",
        "ai_community_reply_drafts",
        "ai_report_drafts",
        "ai_approval_audit_events",
    }
    brand = _make_brand()
    object_ids: list[tuple[str, str]] = []
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename = ANY($1::text[])
                """,
                list(required_tables),
            )
            assert {row["tablename"] for row in rows} == required_tables

        repository = AIPersistenceRepository(pool)
        await repository.save_brand_profile(brand)

        memory = BrandMemory(repository, allow_profile_bootstrap=False)
        loaded = await memory.load_brand_profile(brand)
        assert loaded.brand_id == brand.brand_id

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
        community = await orchestrator.analyze_community_message(
            CommunityManagementRequest(
                brand_profile=brand,
                platform="instagram",
                message_text="Can someone help with my order today?",
            )
        )
        community_draft = await repository.save_community_reply_draft(
            brand_id=brand.brand_id,
            analysis=community,
            metadata={"platform": "instagram", "phase": "phase_5_live_test"},
        )
        report = await orchestrator.generate_report_insights(
            ReportingInsightRequest(
                brand_profile=brand,
                reporting_period="2026-06",
                platforms=["linkedin"],
                analytics_data={"impressions": 1200, "engagement_rate": 0.07},
                campaign_goals=["trust"],
            )
        )
        report_draft = await repository.save_report_draft(
            brand_id=brand.brand_id,
            report_type="monthly",
            date_range="2026-06",
            insight_payload=report.model_dump(mode="json"),
            recommendations=report.recommended_changes,
            metadata={"phase": "phase_5_live_test"},
        )

        async with pool.acquire() as conn:
            content_draft_id = str(
                await conn.fetchval(
                    "SELECT draft_id FROM ai_content_drafts WHERE brand_id = $1 ORDER BY created_at DESC LIMIT 1",
                    brand.brand_id,
                )
            )
            calendar_item_id = str(
                await conn.fetchval(
                    "SELECT calendar_item_id FROM ai_calendar_draft_items WHERE brand_id = $1 ORDER BY created_at DESC LIMIT 1",
                    brand.brand_id,
                )
            )
            review_count = await conn.fetchval("SELECT count(*) FROM ai_quality_reviews WHERE brand_id = $1", brand.brand_id)

        assert package.quality_scores is not None
        assert package.quality_scores.approval_status == "requires_human_review"
        assert calendar.approval_required is True
        assert review_count >= 1
        assert community_draft["auto_reply_allowed"] is False
        assert report_draft["approval_status"] == "draft"

        service = ApprovalService(repository)
        object_ids.extend(
            [
                ("content_draft", content_draft_id),
                ("calendar_draft", calendar_item_id),
                ("community_reply", str(community_draft["reply_draft_id"])),
                ("report_draft", str(report_draft["report_draft_id"])),
            ]
        )

        await service.apply_decision(
            ApprovalDecision(
                object_id=content_draft_id,
                object_type=ApprovalObjectType.CONTENT_DRAFT,
                new_status=ApprovalStatus.IN_REVIEW,
                action=ApprovalAction.SUBMIT,
            )
        )
        approved_content = await service.apply_decision(
            ApprovalDecision(
                object_id=content_draft_id,
                object_type=ApprovalObjectType.CONTENT_DRAFT,
                new_status=ApprovalStatus.APPROVED,
                action=ApprovalAction.APPROVE,
            )
        )
        await service.apply_decision(
            ApprovalDecision(
                object_id=calendar_item_id,
                object_type=ApprovalObjectType.CALENDAR_DRAFT,
                new_status=ApprovalStatus.IN_REVIEW,
                action=ApprovalAction.SUBMIT,
            )
        )
        await service.apply_decision(
            ApprovalDecision(
                object_id=calendar_item_id,
                object_type=ApprovalObjectType.CALENDAR_DRAFT,
                new_status=ApprovalStatus.APPROVED,
                action=ApprovalAction.APPROVE,
            )
        )
        ready_calendar = await service.apply_decision(
            ApprovalDecision(
                object_id=calendar_item_id,
                object_type=ApprovalObjectType.CALENDAR_DRAFT,
                new_status=ApprovalStatus.READY_FOR_SCHEDULING,
                action=ApprovalAction.MARK_READY_FOR_SCHEDULING,
            )
        )
        await service.apply_decision(
            ApprovalDecision(
                object_id=str(community_draft["reply_draft_id"]),
                object_type=ApprovalObjectType.COMMUNITY_REPLY,
                new_status=ApprovalStatus.IN_REVIEW,
                action=ApprovalAction.SUBMIT,
            )
        )
        approved_reply = await service.apply_decision(
            ApprovalDecision(
                object_id=str(community_draft["reply_draft_id"]),
                object_type=ApprovalObjectType.COMMUNITY_REPLY,
                new_status=ApprovalStatus.APPROVED,
                action=ApprovalAction.APPROVE,
            )
        )

        content_audit = await service.list_audit_events(ApprovalObjectType.CONTENT_DRAFT, content_draft_id)
        calendar_queue = await repository.list_calendar_drafts(brand_id=brand.brand_id, status="ready_for_scheduling")
        community_queue = await repository.list_community_reply_drafts(brand_id=brand.brand_id, status="approved")
        report_queue = await repository.list_report_drafts(brand_id=brand.brand_id, status="draft")

        assert approved_content.record["approval_status"] == "approved"
        assert ready_calendar.record["approval_status"] == "ready_for_scheduling"
        assert approved_reply.record["auto_reply_allowed"] is False
        assert len(content_audit) == 2
        assert calendar_queue
        assert community_queue[0]["auto_reply_allowed"] is False
        assert report_queue
    finally:
        async with pool.acquire() as conn:
            for object_type, object_id in object_ids:
                await conn.execute(
                    "DELETE FROM ai_approval_audit_events WHERE object_type = $1 AND object_id = $2",
                    object_type,
                    object_id,
                )
            await conn.execute("DELETE FROM ai_brand_memory WHERE brand_id = $1", brand.brand_id)
        await pool.close()
