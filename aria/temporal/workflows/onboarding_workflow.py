# filename: temporal/workflows/onboarding_workflow.py
# purpose: Temporal onboarding workflow coordinating tone/visual analysis, quality checks, and test post generation.
# dependencies: datetime, temporalio.workflow, temporalio.activity, db.connection, flows.onboarding

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import activity, workflow

from db.connection import get_pool, init_pool
from flows.onboarding import OnboardingOrchestrator


@activity.defn
async def run_tone_fingerprint(company_id: str) -> dict[str, Any]:
    await init_pool()
    orchestrator = OnboardingOrchestrator(get_pool())
    return await orchestrator.brand_analyzer.run_tone_fingerprint(company_id)


@activity.defn
async def run_visual_extraction(company_id: str) -> dict[str, Any]:
    await init_pool()
    orchestrator = OnboardingOrchestrator(get_pool())
    return await orchestrator.brand_analyzer.run_visual_extraction(company_id)


@activity.defn
async def run_quality_check(company_id: str) -> dict[str, Any]:
    await init_pool()
    orchestrator = OnboardingOrchestrator(get_pool())
    return await orchestrator.run_quality_check(company_id)


@activity.defn
async def generate_first_test_post(company_id: str) -> dict[str, Any]:
    await init_pool()
    orchestrator = OnboardingOrchestrator(get_pool())
    return await orchestrator.generate_first_test_post(company_id)


@workflow.defn
class OnboardingWorkflow:
    @workflow.run
    async def run(self, company_id: str) -> dict[str, Any]:
        step_timeout = timedelta(minutes=5)

        a1 = workflow.start_activity(
            run_tone_fingerprint,
            company_id,
            start_to_close_timeout=step_timeout,
        )
        a2 = workflow.start_activity(
            run_visual_extraction,
            company_id,
            start_to_close_timeout=step_timeout,
        )
        tone = await a1
        visual = await a2

        qc = await workflow.execute_activity(
            run_quality_check,
            company_id,
            start_to_close_timeout=step_timeout,
        )

        score = float(qc.get("score", 0.0))
        if score < 70.0:
            return {
                "status": "remediation_required",
                "remediation": qc.get("remediation", []),
            }

        test_post = await workflow.execute_activity(
            generate_first_test_post,
            company_id,
            start_to_close_timeout=step_timeout,
        )
        return {
            "status": "complete",
            "quality_score": score,
            "test_post": test_post,
        }
