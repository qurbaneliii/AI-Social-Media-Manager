# FILE: apps/time-optimization/router.py
from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends
from opentelemetry import trace

from config import Settings
from dependencies import get_settings_dep
from exceptions import ModuleProcessingError
from models.input import TimeOptimizationInput
from models.output import TimeOptimizationOutput
from services.core_logic import TimeOptimizationService
from types_shared import HealthResponse

router = APIRouter()
log = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return HealthResponse(module="time-optimization", version=settings.service_version)


@router.post("/run", response_model=TimeOptimizationOutput)
async def run_time_optimization(
    payload: TimeOptimizationInput,
    settings: Settings = Depends(get_settings_dep),
) -> TimeOptimizationOutput:
    try:
        with tracer.start_as_current_span("time_optimization.run") as span:
            span.set_attribute("company_id", str(payload.company_id))
            result = await TimeOptimizationService(settings).run(payload)
            span.set_attribute("confidence_score", result.confidence_score)
            return result
    except ModuleProcessingError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("processing_error", trace_id=str(uuid4()), error=str(exc))
        raise ModuleProcessingError("processing_error", "Time optimization failed", True) from exc
