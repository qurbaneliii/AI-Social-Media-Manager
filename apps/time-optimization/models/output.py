# FILE: apps/time-optimization/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import Platform, StrictBaseModel


class RankedWindow(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    dow: int = Field(..., ge=0, le=6)
    hour: int = Field(..., ge=0, le=23)
    score: float = Field(..., ge=0.0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class TimeOptimizationOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    windows: list[RankedWindow]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    degraded_mode: bool = False
    generated_at: datetime
