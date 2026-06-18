from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from .brand import BrandProfile


class ContentCalendarItem(BaseModel):
    date: date
    time: time
    platform: str
    content_pillar: str
    objective: str
    topic: str
    content_type: str
    draft_status: str = "draft"
    rationale: str
    approval_required: bool = True


class CalendarPlanningRequest(BaseModel):
    brand_profile: BrandProfile
    start_date: date
    end_date: date
    platforms: list[str] = Field(default_factory=list)
    content_pillars: list[str] = Field(default_factory=list)
    campaign_objectives: list[str] = Field(default_factory=list)
    posting_frequency_per_week: int = Field(default=3, ge=1, le=21)
    preferred_content_types: list[str] = Field(default_factory=list)
    timezone: str = "UTC"


class ContentCalendarPlan(BaseModel):
    items: list[ContentCalendarItem] = Field(default_factory=list)
    rationale: str
    risk_notes: list[str] = Field(default_factory=list)
    approval_required: bool = True
