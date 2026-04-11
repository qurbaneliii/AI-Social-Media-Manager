# FILE: packages/types/shared/pagination.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaginationRequest(BaseModel):
    """Implements Section 3 shared pagination request model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class PaginationResponse(BaseModel):
    """Implements Section 3 shared pagination response metadata model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
