# FILE: apps/scheduler/services/temporal_workflows.py
from __future__ import annotations

import random
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from services.temporal_activities import metrics_ingest, publish_attempt, validate_request


RETRY_SCHEDULE_SECONDS = [60, 300, 900, 2700, 7200]
JITTER_COEFFICIENT = 0.20


@workflow.defn
class PostGenerationWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        """Run generation workflow validation and completion marker."""
        validated = await workflow.execute_activity(validate_request, data, start_to_close_timeout=timedelta(seconds=30))
        return {"status": "generated", **validated}


@workflow.defn
class PostPublishWorkflow:
    def __init__(self) -> None:
        self._approved = False

    @workflow.signal
    async def approve(self) -> None:
        self._approved = True

    @workflow.run
    async def run(self, data: dict) -> dict:
        """Execute publish flow with approval wait, retries, and dead-letter fallback."""
        validated = await workflow.execute_activity(validate_request, data, start_to_close_timeout=timedelta(seconds=30))

        if validated.get("approval_mode") == "human":
            approved = await workflow.wait_condition(lambda: self._approved, timeout=timedelta(hours=48))
            if not approved:
                return {"status": "expired", **validated}

        last_error = ""
        for delay in RETRY_SCHEDULE_SECONDS:
            try:
                return await workflow.execute_activity(publish_attempt, validated, start_to_close_timeout=timedelta(seconds=60))
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                jitter = 1.0 + random.uniform(-JITTER_COEFFICIENT, JITTER_COEFFICIENT)
                await workflow.sleep(timedelta(seconds=int(delay * jitter)))

        return {"status": "dead_letter", "error": last_error, **validated}


@workflow.defn
class PerformanceFeedbackWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        """Run delayed feedback ingestion and update status."""
        await workflow.sleep(timedelta(hours=6))
        result = await workflow.execute_activity(metrics_ingest, data, start_to_close_timeout=timedelta(seconds=60))
        return {"status": "feedback_complete", **result}
