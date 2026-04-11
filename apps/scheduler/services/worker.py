# FILE: apps/scheduler/services/worker.py
from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from services.temporal_activities import metrics_ingest, publish_attempt, validate_request
from services.temporal_workflows import PerformanceFeedbackWorkflow, PostGenerationWorkflow, PostPublishWorkflow


async def run_worker(address: str, task_queue: str, namespace: str) -> None:
    """Start Temporal worker with scheduler workflows and activities."""
    client = await Client.connect(address, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[PostGenerationWorkflow, PostPublishWorkflow, PerformanceFeedbackWorkflow],
        activities=[validate_request, publish_attempt, metrics_ingest],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker("temporal:7233", "aria-task-queue", "default"))
