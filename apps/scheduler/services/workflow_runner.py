# FILE: apps/scheduler/services/workflow_runner.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from temporalio.client import Client

from config import Settings
from models.input import WorkflowRunInput
from models.output import WorkflowRunOutput
from services.temporal_workflows import PerformanceFeedbackWorkflow, PostGenerationWorkflow, PostPublishWorkflow


class WorkflowRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def process(self, payload: WorkflowRunInput) -> WorkflowRunOutput:
        """Start requested Temporal workflow and return run metadata."""
        client = await Client.connect(self.settings.temporal_address, namespace=self.settings.temporal_namespace)
        workflow_id = f"{payload.workflow_name}-{uuid4()}"

        if payload.workflow_name == "PostGenerationWorkflow":
            handle = await client.start_workflow(
                PostGenerationWorkflow.run,
                payload.model_dump(mode="json"),
                id=workflow_id,
                task_queue=self.settings.temporal_task_queue,
            )
            status = "started"
        elif payload.workflow_name == "PostPublishWorkflow":
            handle = await client.start_workflow(
                PostPublishWorkflow.run,
                payload.model_dump(mode="json"),
                id=workflow_id,
                task_queue=self.settings.temporal_task_queue,
            )
            status = "started"
        else:
            handle = await client.start_workflow(
                PerformanceFeedbackWorkflow.run,
                payload.model_dump(mode="json"),
                id=workflow_id,
                task_queue=self.settings.temporal_task_queue,
            )
            status = "started"

        return WorkflowRunOutput(
            workflow_id=handle.id,
            run_id=handle.first_execution_run_id,
            status=status,
            generated_at=datetime.now(tz=timezone.utc),
        )
