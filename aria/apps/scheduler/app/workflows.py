from __future__ import annotations

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from . import activities


@workflow.defn
class PostGenerationWorkflow:
    @workflow.run
    async def run(self, request: dict) -> dict:
        validated = await workflow.execute_activity(
            activities.validate_request,
            request,
            start_to_close_timeout=timedelta(seconds=15),
        )

        parallel = await workflow.execute_activity(
            activities.trigger_parallel_modules,
            validated,
            start_to_close_timeout=timedelta(seconds=40),
        )

        # Compensation behavior: if module wait exceeds timeout, fallback defaults are used.
        try:
            module_results = await workflow.execute_activity(
                activities.wait_for_module_results,
                parallel,
                start_to_close_timeout=timedelta(seconds=40),
            )
        except Exception:
            module_results = {
                "content": {"ok": False, "fallback": True},
                "visual": {"ok": False, "fallback": True},
                "hashtag": {"ok": False, "fallback": True},
                "audience": {"ok": False, "fallback": True},
                "time": {"ok": False, "fallback": True},
            }

        scored = await workflow.execute_activity(
            activities.consolidate_and_score,
            module_results,
            start_to_close_timeout=timedelta(seconds=20),
        )

        delivered = await workflow.execute_activity(
            activities.deliver_package,
            scored,
            start_to_close_timeout=timedelta(seconds=5),
        )

        return delivered


@workflow.defn
class PostPublishWorkflow:
    @workflow.run
    async def run(self, request: dict) -> dict:
        creds = await workflow.execute_activity(
            activities.load_credentials,
            request,
            start_to_close_timeout=timedelta(seconds=10),
        )

        gate = await workflow.execute_activity(
            activities.approval_gate,
            creds,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if gate.get("paused"):
            return {"status": "paused_for_approval", **gate}

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=10),
            maximum_interval=timedelta(seconds=300),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        try:
            published = await workflow.execute_activity(
                activities.publish_to_adapter,
                gate,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            confirmed = await workflow.execute_activity(
                activities.confirm_external_id,
                published,
                start_to_close_timeout=timedelta(seconds=10),
            )
            scheduled = await workflow.execute_activity(
                activities.schedule_metrics_pull,
                confirmed,
                start_to_close_timeout=timedelta(seconds=10),
            )
            return {"status": "published", **scheduled}
        except Exception:
            dead = await workflow.execute_activity(
                activities.emit_dead_letter,
                gate,
                start_to_close_timeout=timedelta(seconds=10),
            )
            notified = await workflow.execute_activity(
                activities.notify_user,
                dead,
                start_to_close_timeout=timedelta(seconds=10),
            )
            return {"status": "failed_dead_letter", **notified}


@workflow.defn
class PerformanceFeedbackWorkflow:
    @workflow.run
    async def run(self, request: dict) -> dict:
        await workflow.sleep(timedelta(hours=6))

        ingested = await workflow.execute_activity(
            activities.ingest_metrics,
            request,
            start_to_close_timeout=timedelta(seconds=20),
        )
        scored = await workflow.execute_activity(
            activities.score_post,
            ingested,
            start_to_close_timeout=timedelta(seconds=20),
        )
        hashtags = await workflow.execute_activity(
            activities.update_hashtag_weights,
            scored,
            start_to_close_timeout=timedelta(seconds=20),
        )
        windows = await workflow.execute_activity(
            activities.update_posting_window_weights,
            hashtags,
            start_to_close_timeout=timedelta(seconds=20),
        )
        threshold = await workflow.execute_activity(
            activities.check_degradation_threshold,
            windows,
            start_to_close_timeout=timedelta(seconds=20),
        )
        recal = await workflow.execute_activity(
            activities.trigger_recalibration_if_needed,
            threshold,
            start_to_close_timeout=timedelta(seconds=20),
        )

        return {"status": "completed", **recal}
