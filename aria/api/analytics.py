# filename: api/analytics.py
# purpose: Analytics ingest endpoint for platform webhook/pull metric payloads.
# dependencies: fastapi, pydantic, memory.feedback

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from memory.feedback import PerformanceIngester

router = APIRouter()


class AnalyticsIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    post_id: str | None = None
    platform: str
    external_post_id: str | None = None
    impressions: int = Field(ge=0)
    reach: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0)
    click_through_rate: float = Field(ge=0.0)
    saves: int = Field(ge=0)
    shares: int = Field(ge=0)
    follower_growth_delta: int = 0
    posting_timestamp: datetime
    captured_at: datetime


@router.post("/ingest")
async def ingest_analytics(payload: AnalyticsIngestRequest, request: Request) -> dict[str, Any]:
    ingester = PerformanceIngester(request.app.state.db_pool)
    await ingester.ingest_webhook(payload.model_dump())
    return {"accepted": True}
