# filename: api/schedules.py
# purpose: Scheduling and webhook API endpoints backed by PostingService and schedules repository.
# dependencies: datetime, asyncpg, fastapi, pydantic, db.connection, flows.posting

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db.connection import set_tenant
from flows.posting import PostingService

router = APIRouter()
webhooks_router = APIRouter()


class ScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_id: str
    company_id: str
    platform: str
    run_at_utc: datetime
    approval_mode: str


@router.post("")
async def create_schedule(payload: ScheduleRequest, request: Request) -> dict[str, Any]:
    service: PostingService = request.app.state.posting_service
    result = await service.schedule_post(
        post_id=payload.post_id,
        company_id=payload.company_id,
        platform=payload.platform,
        run_at_utc=payload.run_at_utc,
        approval_mode=payload.approval_mode,
    )
    return {
        "schedule_id": result["schedule_id"],
        "workflow_id": result["workflow_id"],
        "status": "queued",
    }


@webhooks_router.post("/{platform}")
async def ingest_webhook(
    platform: str,
    request: Request,
    x_signature: str = Header(default="", alias="X-Signature"),
) -> dict[str, bool]:
    service: PostingService = request.app.state.posting_service
    raw = await request.body()
    result = await service.handle_webhook(raw_body=raw, signature=x_signature, platform=platform)
    return {"accepted": bool(result.get("accepted", False))}


@router.get("/{schedule_id}")
async def get_schedule(schedule_id: str, company_id: str, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            row = await conn.fetchrow("SELECT * FROM schedules WHERE schedule_id = $1::uuid", schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return dict(row)
