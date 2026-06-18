from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brand import BrandProfile


class ReportingInsightRequest(BaseModel):
    brand_profile: BrandProfile
    reporting_period: str
    platforms: list[str] = Field(default_factory=list)
    analytics_data: dict[str, Any] = Field(default_factory=dict)
    campaign_goals: list[str] = Field(default_factory=list)


class ReportInsights(BaseModel):
    summary: str
    wins: list[str] = Field(default_factory=list)
    misses: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    chart_ready_data: dict[str, Any] = Field(default_factory=dict)


class ReportingInsightReport(BaseModel):
    summary: str
    what_worked: list[str] = Field(default_factory=list)
    what_failed: list[str] = Field(default_factory=list)
    recommended_changes: list[str] = Field(default_factory=list)
    next_experiments: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    chart_ready_data: dict[str, Any] = Field(default_factory=dict)
