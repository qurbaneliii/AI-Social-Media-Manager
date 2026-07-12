from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from ai.schemas.brand import BrandProfile, BrandProfileValidationResult


class SessionResponse(BaseModel):
    user_id: str
    email: str | None = None
    role: str
    workspace_id: str
    workspace_name: str
    timezone: str
    brand_id: str | None = None
    brand_name: str | None = None


class BrandProfileRecord(BaseModel):
    profile: BrandProfile
    validation: BrandProfileValidationResult
    profile_version: int
    updated_at: datetime | None = None


class BrandProfileUpdate(BaseModel):
    profile: BrandProfile
    expected_version: int | None = Field(default=None, ge=0)


class PageMeta(BaseModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class ContentPage(BaseModel):
    items: list[dict[str, Any]]
    page: PageMeta


class CalendarCreate(BaseModel):
    content_draft_id: str
    platform: str
    planned_at: datetime
    timezone: str = "UTC"


class CalendarUpdate(BaseModel):
    planned_at: datetime | None = None
    timezone: str | None = None
    planning_state: Literal["draft_plan", "awaiting_approval", "approved_internal", "ready_for_scheduling", "failed"] | None = None


class CalendarPage(BaseModel):
    items: list[dict[str, Any]]
    page: PageMeta
    external_scheduling: Literal["unavailable"] = "unavailable"
    publishing: Literal["unavailable"] = "unavailable"


class CapabilityStatus(BaseModel):
    status: Literal["Available", "Configured", "Demo", "Degraded", "Unavailable"]
    detail: str
    interactive: bool = False


class CapabilitiesResponse(BaseModel):
    database: CapabilityStatus
    authentication: CapabilityStatus
    ai_provider: CapabilityStatus
    ai_mock_mode: CapabilityStatus
    media_storage: CapabilityStatus
    external_scheduling: CapabilityStatus
    publishing: CapabilityStatus
    external_analytics: CapabilityStatus
    background_workers: CapabilityStatus
