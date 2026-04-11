# FILE: apps/scheduler/router.py
from __future__ import annotations

from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, Header
from opentelemetry import trace

from config import Settings
from dependencies import get_db_pool, get_llm_client, get_settings_dep
from exceptions import ModuleProcessingError
from models.input import WebhookInput, WorkflowRunInput
from models.output import WebhookOutput, WorkflowRunOutput
from services.core_logic import SchedulerService
from types_shared import HealthResponse

router = APIRouter()
tracer = trace.get_tracer(__name__)
log = structlog.get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="scheduler", version=settings.service_version)


@router.post("/run", response_model=WorkflowRunOutput)
async def run_scheduler(
    payload: WorkflowRunInput,
    settings: Settings = Depends(get_settings_dep),
    db_pool=Depends(get_db_pool),
    llm_client=Depends(get_llm_client),
) -> WorkflowRunOutput:
    try:
        with tracer.start_as_current_span("scheduler.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            span.set_attribute("platform", payload.platform.value)
            result = await SchedulerService(settings, db_pool, llm_client).run_workflow(payload)
            span.set_attribute("confidence_score", 1.0)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("processing_error", trace_id=str(uuid4()), error=str(exc))
        raise ModuleProcessingError("processing_error", "Workflow execution failed", True) from exc


@router.post("/webhook", response_model=WebhookOutput)
async def webhook(
    payload: WebhookInput,
    x_company_id: UUID = Header(...),
    x_kms_secret: str = Header(...),
    settings: Settings = Depends(get_settings_dep),
    db_pool=Depends(get_db_pool),
    llm_client=Depends(get_llm_client),
) -> WebhookOutput:
    return await SchedulerService(settings, db_pool, llm_client).handle_webhook(payload, x_kms_secret, x_company_id)
