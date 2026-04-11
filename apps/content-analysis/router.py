# FILE: apps/content-analysis/router.py
from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Request
from opentelemetry import trace

from config import Settings
from dependencies import get_db_pool, get_llm_client, get_settings_dep, get_vector_db
from exceptions import ModuleProcessingError
from models.input import ContentAnalysisInput
from models.output import ContentAnalysisOutput
from services.core_logic import ContentAnalysisService
from types_shared import HealthResponse

log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="content-analysis", version=settings.service_version)


@router.post("/run", response_model=ContentAnalysisOutput)
async def run_content_analysis(
    payload: ContentAnalysisInput,
    request: Request,
    settings: Settings = Depends(get_settings_dep),
    db_pool=Depends(get_db_pool),
    vector_db_pool=Depends(get_vector_db),
    llm_client=Depends(get_llm_client),
) -> ContentAnalysisOutput:
    try:
        with tracer.start_as_current_span("content_analysis.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            service = ContentAnalysisService(settings, request.app.state.nlp_model, db_pool, vector_db_pool, llm_client)
            result = await service.run(payload)
            span.set_attribute("confidence_score", result.confidence_score)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        trace_id = str(uuid4())
        log.error("processing_error", trace_id=trace_id, error=str(exc))
        raise ModuleProcessingError("processing_error", "Content analysis failed", True) from exc
