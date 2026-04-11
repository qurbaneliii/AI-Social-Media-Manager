# FILE: packages/types/shared/errors.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Implements Section 3 shared service error envelope detail model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    code: Annotated[str, Field(min_length=3, max_length=50, pattern=r"^[A-Z_]+$")]
    message: Annotated[str, Field(min_length=5, max_length=500)]
    retryable: bool
    trace_id: UUID


class FieldError(BaseModel):
    """Implements Section 3 shared field-level validation error model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    field: Annotated[str, Field(min_length=1, max_length=255)]
    message: Annotated[str, Field(min_length=1, max_length=500)]
    rejected_value: Annotated[str, Field(min_length=1, max_length=500)] | None = None


class ValidationErrorResponse(BaseModel):
    """Implements Section 3 shared validation error response model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    errors: Annotated[list[FieldError], Field(min_length=1)]
    trace_id: UUID


class ServiceUnavailableResponse(BaseModel):
    """Implements Section 3 shared service unavailable response model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    error: ErrorDetail
    retry_after_seconds: int | None = Field(default=None, ge=0)
