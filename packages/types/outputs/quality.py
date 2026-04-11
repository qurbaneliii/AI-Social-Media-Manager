# FILE: packages/types/outputs/quality.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums import ReadingLevel, RiskFlag


class QualityOutput(BaseModel):
    """Implements Section 3.2.6 Output F quality and risk assessment response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    post_id: UUID
    overall_score: float = Field(ge=0.0, le=1.0)
    policy_compliance_score: float = Field(ge=0.0, le=1.0)
    reading_level: ReadingLevel
    risk_flags: Annotated[list[RiskFlag], Field(default_factory=list, max_length=20)]
    rationale: Annotated[str, Field(max_length=500)] | None = None
    requires_human_review: bool = False
    generated_at: datetime

    @field_validator("risk_flags")
    @classmethod
    def validate_unique_risk_flags(cls, value: list[RiskFlag]) -> list[RiskFlag]:
        """Ensures risk flags are not duplicated."""
        if len({str(item) for item in value}) != len(value):
            raise ValueError("risk_flags must be unique")
        return value
