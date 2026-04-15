# filename: api/schedules.py
# purpose: Scheduling and webhook API endpoints backed by PostingService and schedules repository.
# dependencies: datetime, asyncpg, fastapi, pydantic, db.connection, flows.posting

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from db.connection import set_tenant
from flows.posting import PostingService

router = APIRouter()
webhooks_router = APIRouter()
SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class ScheduleTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    run_at_utc: datetime


class ScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_id: str
    company_id: str
    targets: list[ScheduleTarget] = Field(min_length=1)
    approval_mode: str
    manual_override: dict[str, Any] | None = None


class ApproveScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str | None = None
    approved_by: str | None = None


@router.post("")
async def create_schedule(payload: ScheduleRequest, request: Request) -> dict[str, Any]:
    service: PostingService = request.app.state.posting_service
    schedule_ids: list[str] = []
    for target in payload.targets:
        result = await service.schedule_post(
            post_id=payload.post_id,
            company_id=payload.company_id,
            platform=target.platform,
            run_at_utc=target.run_at_utc,
            approval_mode=payload.approval_mode,
        )
        schedule_ids.append(result["schedule_id"])

    return {
        "schedule_ids": schedule_ids,
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
async def get_schedule(schedule_id: str, request: Request, company_id: str | None = None) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            if company_id:
                await set_tenant(conn, company_id)
            else:
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            row = await conn.fetchrow("SELECT * FROM schedules WHERE schedule_id = $1::uuid", schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return dict(row)


@router.post("/{schedule_id}/approve")
async def approve_schedule(
    schedule_id: str,
    request: Request,
    payload: ApproveScheduleRequest | None = None,
) -> dict[str, Any]:
    company_id = payload.company_id if payload else None
    approved_by = payload.approved_by if payload else None

    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            if company_id:
                await set_tenant(conn, company_id)
            else:
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")

            row = await conn.fetchrow(
                """
                UPDATE schedules
                SET status = CASE WHEN status = 'awaiting_approval' THEN 'queued' ELSE status END,
                    approved_at = now(),
                    approved_by = COALESCE($2::uuid, approved_by)
                WHERE schedule_id = $1::uuid
                RETURNING schedule_id, status, approved_at, approved_by
                """,
                schedule_id,
                approved_by,
            )

    if row is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "approved": True,
        "schedule_id": str(row["schedule_id"]),
        "status": str(row["status"]),
        "approved_at": row["approved_at"],
        "approved_by": str(row["approved_by"]) if row["approved_by"] else None,
    }
