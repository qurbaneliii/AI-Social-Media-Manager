# FILE: apps/content-analysis/models/output.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import StrictBaseModel


class ToneFingerprint(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, float] = Field(default_factory=dict)
    top_terms: list[str] = Field(default_factory=list)
    dominant_topics: list[str] = Field(default_factory=list)


class ContentAnalysisOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    tone_fingerprint: ToneFingerprint
    embedding_dim: int = Field(..., ge=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    translated: bool = Field(default=False)
    degraded_mode: bool = Field(default=False)
    generated_at: datetime
