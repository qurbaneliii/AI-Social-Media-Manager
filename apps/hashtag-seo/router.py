# FILE: apps/hashtag-seo/router.py
from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends
from opentelemetry import trace

from config import Settings
from dependencies import get_llm_client, get_redis, get_settings_dep, get_vector_db
from exceptions import ModuleProcessingError
from models.input import HashtagSeoInput
from models.output import HashtagSeoOutput
from services.core_logic import HashtagSeoService
from types_shared import HealthResponse

router = APIRouter()
log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="hashtag-seo", version=settings.service_version)


@router.post("/run", response_model=HashtagSeoOutput)
async def run_hashtag(
    payload: HashtagSeoInput,
    settings: Settings = Depends(get_settings_dep),
    llm_client=Depends(get_llm_client),
    vector_db=Depends(get_vector_db),
    redis_client=Depends(get_redis),
) -> HashtagSeoOutput:
    try:
        with tracer.start_as_current_span("hashtag_seo.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            span.set_attribute("platform", payload.target_platform.value)
            result = await HashtagSeoService(settings, llm_client, vector_db, redis_client).run(payload)
            span.set_attribute("confidence_score", result.confidence_score)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("processing_error", trace_id=str(uuid4()), error=str(exc))
        raise ModuleProcessingError("processing_error", "Hashtag/SEO processing failed", True) from exc
