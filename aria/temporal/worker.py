# filename: temporal/worker.py
# purpose: Temporal worker bootstrap registering onboarding and posting workflows with all required activities.
# dependencies: os, asyncio, temporalio.client, temporalio.worker, temporal workflows

from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from temporal.workflows.onboarding_workflow import (
    OnboardingWorkflow,
    generate_first_test_post,
    run_quality_check,
    run_tone_fingerprint,
    run_visual_extraction,
)
from temporal.workflows.posting_workflow import (
    PostingWorkflow,
    fetch_schedule,
    handle_publish_failure,
    publish_to_platform,
    wait_for_approval,
)


async def run_worker() -> None:
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "aria-main")
    client = await Client.connect(host, namespace=namespace)

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[PostingWorkflow, OnboardingWorkflow],
        activities=[
            fetch_schedule,
            wait_for_approval,
            publish_to_platform,
            handle_publish_failure,
            run_tone_fingerprint,
            run_visual_extraction,
            run_quality_check,
            generate_first_test_post,
        ],
    )
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
