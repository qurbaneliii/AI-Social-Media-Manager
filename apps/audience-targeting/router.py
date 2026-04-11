# FILE: apps/audience-targeting/router.py
from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends
from opentelemetry import trace

from config import Settings
from dependencies import get_db_pool, get_llm_client, get_redis, get_settings_dep
from exceptions import ModuleProcessingError
from models.input import AudienceTargetingInput
from models.output import AudienceTargetingOutput
from services.core_logic import AudienceTargetingService
from types_shared import HealthResponse

router = APIRouter()
log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="audience-targeting", version=settings.service_version)


@router.post("/run", response_model=AudienceTargetingOutput)
async def run_targeting(
    payload: AudienceTargetingInput,
    settings: Settings = Depends(get_settings_dep),
    db_pool=Depends(get_db_pool),
    redis_client=Depends(get_redis),
    llm_client=Depends(get_llm_client),
) -> AudienceTargetingOutput:
    try:
        with tracer.start_as_current_span("audience_targeting.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            result = await AudienceTargetingService(settings, db_pool, redis_client, llm_client).run(payload)
            span.set_attribute("confidence_score", result.confidence_score)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("processing_error", trace_id=str(uuid4()), error=str(exc))
        raise ModuleProcessingError("processing_error", "Audience targeting failed", True) from exc
