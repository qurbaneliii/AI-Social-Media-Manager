from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import (
    approval_gate,
    check_degradation_threshold,
    confirm_external_id,
    consolidate_and_score,
    deliver_package,
    emit_dead_letter,
    ingest_metrics,
    load_credentials,
    notify_user,
    publish_to_adapter,
    schedule_metrics_pull,
    score_post,
    trigger_parallel_modules,
    trigger_recalibration_if_needed,
    update_hashtag_weights,
    update_posting_window_weights,
    validate_request,
    wait_for_module_results,
)
from .workflows import PerformanceFeedbackWorkflow, PostGenerationWorkflow, PostPublishWorkflow


async def run_worker(address: str = "localhost:7233", task_queue: str = "aria-task-queue") -> None:
    client = await Client.connect(address)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[PostGenerationWorkflow, PostPublishWorkflow, PerformanceFeedbackWorkflow],
        activities=[
            validate_request,
            trigger_parallel_modules,
            wait_for_module_results,
            consolidate_and_score,
            deliver_package,
            load_credentials,
            approval_gate,
            publish_to_adapter,
            confirm_external_id,
            schedule_metrics_pull,
            emit_dead_letter,
            notify_user,
            ingest_metrics,
            score_post,
            update_hashtag_weights,
            update_posting_window_weights,
            check_degradation_threshold,
            trigger_recalibration_if_needed,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
