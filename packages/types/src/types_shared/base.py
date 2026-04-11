# FILE: packages/types/src/types_shared/base.py
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ErrorBody(StrictBaseModel):
    code: str = Field(..., min_length=2, max_length=100, description="Machine-readable error code")
    message: str = Field(..., min_length=2, max_length=500, description="Human-readable error message")
    retryable: bool = Field(..., description="Indicates whether retrying may succeed")
    trace_id: UUID = Field(..., description="Trace identifier")


class ErrorEnvelope(StrictBaseModel):
    error: ErrorBody


class HealthResponse(StrictBaseModel):
    status: str = Field(default="ok", pattern="^ok$")
    module: str = Field(..., min_length=2, max_length=120)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
