# FILE: apps/visual-understanding/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import StrictBaseModel


class ClusterColor(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    ratio: float = Field(..., ge=0.0, le=1.0)


class VisualUnderstandingOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    style_label: str
    layout_type: str
    typography_style: str
    colors: list[ClusterColor]
    brand_consistency_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    degraded: bool = False
    generated_at: datetime
