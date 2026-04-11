# FILE: packages/types/outputs/schedule.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import ApprovalMode, Platform, ReasonCode, ScheduleStatus


class RankedWindow(BaseModel):
    """Implements Section 3.2.4 Output D ranked schedule window model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    platform: Platform
    dow: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    score: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: Annotated[list[ReasonCode], Field(min_length=1, max_length=6)]

    @field_validator("reason_codes")
    @classmethod
    def validate_unique_reason_codes(cls, value: list[ReasonCode]) -> list[ReasonCode]:
        """Ensures reason codes are unique within a window."""
        if len({str(item) for item in value}) != len(value):
            raise ValueError("reason_codes must be unique")
        return value


class ScheduledTarget(BaseModel):
    """Implements Section 3.2.4 Output D scheduled target model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    platform: Platform
    run_at_utc: datetime
    status: ScheduleStatus = ScheduleStatus.queued


class ScheduleOutput(BaseModel):
    """Implements Section 3.2.4 Output D scheduling response model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    post_id: UUID
    company_id: UUID
    windows: Annotated[list[RankedWindow], Field(min_length=1, max_length=100)]
    targets: Annotated[list[ScheduledTarget], Field(min_length=1, max_length=20)]
    approval_mode: ApprovalMode
    generated_at: datetime

    @model_validator(mode="after")
    def validate_targets_cover_windows(self) -> "ScheduleOutput":
        """Ensures each target platform exists in generated windows."""
        window_platforms = {str(window.platform) for window in self.windows}
        missing = sorted({str(target.platform) for target in self.targets} - window_platforms)
        if missing:
            raise ValueError(f"Target platforms not present in windows: {missing}")
        return self
