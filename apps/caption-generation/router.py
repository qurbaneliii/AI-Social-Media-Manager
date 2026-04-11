# FILE: apps/caption-generation/router.py
from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends
from opentelemetry import trace

from config import Settings
from dependencies import get_llm_client, get_settings_dep
from exceptions import ModuleProcessingError
from models.input import CaptionGenerationInput
from models.output import CaptionGenerationOutput
from services.core_logic import CaptionGenerationService
from types_shared import HealthResponse

router = APIRouter()
log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="caption-generation", version=settings.service_version)


@router.post("/run", response_model=CaptionGenerationOutput)
async def run_caption(
    payload: CaptionGenerationInput,
    settings: Settings = Depends(get_settings_dep),
    llm_client=Depends(get_llm_client),
) -> CaptionGenerationOutput:
    try:
        with tracer.start_as_current_span("caption_generation.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            result = await CaptionGenerationService(settings, llm_client).run(payload)
            span.set_attribute("confidence_score", result.confidence_score)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("processing_error", trace_id=str(uuid4()), error=str(exc))
        raise ModuleProcessingError("processing_error", "Caption generation failed", True) from exc
