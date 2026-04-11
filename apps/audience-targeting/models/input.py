# FILE: apps/audience-targeting/models/input.py
from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import Platform, StrictBaseModel


class AudienceTargetingInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID
    industry_vertical: str = Field(..., min_length=2, max_length=80)
    target_platforms: list[Platform] = Field(..., min_length=1)
    campaign_context: str = Field(..., min_length=5, max_length=2000)
