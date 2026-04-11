from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel
from temporalio.client import Client

from .learning import MetricPoint, run_learning_cycle
from .workflows import PerformanceFeedbackWorkflow, PostGenerationWorkflow, PostPublishWorkflow


class TriggerRequest(BaseModel):
    workflow: str
    payload: dict


class LearningRequest(BaseModel):
    metrics: list[dict]
    current_hashtag_weights: dict[str, float]
    hourly_performance: dict[int, float]
    previous_prompt_score: float
    current_prompt_score: float
    term_weights: dict[str, float]


app = FastAPI(title="ARIA Scheduler and Automation Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "scheduler"}


@app.post("/run")
async def run_workflow(trigger: TriggerRequest) -> dict:
    client = await Client.connect("localhost:7233")

    if trigger.workflow == "PostGenerationWorkflow":
        handle = await client.start_workflow(
            PostGenerationWorkflow.run,
            trigger.payload,
            id=f"post-generation-{uuid4()}",
            task_queue="aria-task-queue",
            execution_timeout=timedelta(seconds=120),
        )
    elif trigger.workflow == "PostPublishWorkflow":
        handle = await client.start_workflow(
            PostPublishWorkflow.run,
            trigger.payload,
            id=f"post-publish-{uuid4()}",
            task_queue="aria-task-queue",
        )
    elif trigger.workflow == "PerformanceFeedbackWorkflow":
        handle = await client.start_workflow(
            PerformanceFeedbackWorkflow.run,
            trigger.payload,
            id=f"performance-feedback-{uuid4()}",
            task_queue="aria-task-queue",
        )
    else:
        return {"error": "Unknown workflow"}

    return {"workflow_id": handle.id, "run_id": handle.first_execution_run_id}


@app.post("/learning/run")
def run_learning(req: LearningRequest) -> dict:
    metrics = [MetricPoint(**m) for m in req.metrics]
    result = run_learning_cycle(
        metrics=metrics,
        current_hashtag_weights=req.current_hashtag_weights,
        hourly_performance=req.hourly_performance,
        previous_prompt_score=req.previous_prompt_score,
        current_prompt_score=req.current_prompt_score,
        term_weights=req.term_weights,
    )
    return {
        "hashtag_weights": result.hashtag_weights,
        "posting_window_weights": result.posting_window_weights,
        "prompt_recalibration_required": result.prompt_recalibration_required,
        "brand_voice_embedding": result.brand_voice_embedding,
        "events": result.events,
    }
