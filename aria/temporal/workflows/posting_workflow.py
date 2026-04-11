# filename: temporal/workflows/posting_workflow.py
# purpose: Temporal posting workflow and activities for approval gating, publication, and failure handling.
# dependencies: asyncio, uuid, datetime, temporalio.workflow, temporalio.activity, db.connection

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from temporalio import activity, workflow

from db.connection import get_pool, init_pool, set_tenant


SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class ApprovalTimeoutError(Exception):
    """Raised when human approval does not arrive within the allowed window."""


@activity.defn
async def fetch_schedule(schedule_id: str) -> dict[str, Any]:
    await init_pool()
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            row = await conn.fetchrow(
                """
                SELECT s.*, p.selected_variant_id
                FROM schedules s
                JOIN posts p ON p.post_id = s.post_id
                WHERE s.schedule_id = $1::uuid
                """,
                schedule_id,
            )
    if row is None:
        raise ValueError("Schedule not found")
    return dict(row)


@activity.defn
async def wait_for_approval(schedule_id: str) -> dict[str, Any]:
    await init_pool()
    pool = get_pool()
    started = datetime.now(timezone.utc)
    timeout_at = started + timedelta(hours=24)

    while datetime.now(timezone.utc) < timeout_at:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
                row = await conn.fetchrow(
                    "SELECT status, approval_mode FROM schedules WHERE schedule_id = $1::uuid",
                    schedule_id,
                )
        if row is None:
            raise ValueError("Schedule not found")

        status = str(row["status"])
        if status in {"queued", "publishing", "published"}:
            return {"approved": True}
        if status == "awaiting_approval":
            await asyncio.sleep(30)
            continue
        if status in {"failed", "dead_letter"}:
            raise ApprovalTimeoutError("Approval flow moved to terminal failure state")

    raise ApprovalTimeoutError("Approval timeout after 24 hours")


@activity.defn
async def publish_to_platform(schedule_id: str) -> dict[str, Any]:
    await init_pool()
    pool = get_pool()

    external_post_id = f"stub-{uuid.uuid4()}"
    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            await conn.execute(
                """
                UPDATE schedules
                SET external_post_id = $2,
                    status = 'published'
                WHERE schedule_id = $1::uuid
                """,
                schedule_id,
                external_post_id,
            )
    return {"external_post_id": external_post_id, "status": "published"}


@activity.defn
async def handle_publish_failure(schedule_id: str) -> dict[str, Any]:
    await init_pool()
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            row = await conn.fetchrow(
                "SELECT retry_count, max_retries FROM schedules WHERE schedule_id = $1::uuid",
                schedule_id,
            )
            if row is None:
                raise ValueError("Schedule not found")

            retry_count = int(row["retry_count"] or 0) + 1
            max_retries = int(row["max_retries"] or 5)
            if retry_count >= max_retries:
                await conn.execute(
                    """
                    UPDATE schedules
                    SET retry_count = $2,
                        status = 'dead_letter'
                    WHERE schedule_id = $1::uuid
                    """,
                    schedule_id,
                    retry_count,
                )
                return {"status": "dead_letter", "retry_count": retry_count}

            delay_seconds = (2 ** retry_count) * 60
            await conn.execute(
                """
                UPDATE schedules
                SET retry_count = $2,
                    next_retry_at = now() + ($3 || ' seconds')::interval,
                    status = 'failed'
                WHERE schedule_id = $1::uuid
                """,
                schedule_id,
                retry_count,
                delay_seconds,
            )
            return {"status": "failed", "retry_count": retry_count}


@workflow.defn
class PostingWorkflow:
    @workflow.run
    async def run(self, schedule_id: str) -> dict[str, Any]:
        step_timeout = timedelta(minutes=5)

        schedule = await workflow.execute_activity(
            fetch_schedule,
            schedule_id,
            start_to_close_timeout=step_timeout,
        )

        approval_mode = str(schedule.get("approval_mode"))
        if approval_mode == "human":
            await workflow.execute_activity(
                wait_for_approval,
                schedule_id,
                start_to_close_timeout=step_timeout,
            )

        try:
            publish_result = await workflow.execute_activity(
                publish_to_platform,
                schedule_id,
                start_to_close_timeout=step_timeout,
            )
            return {
                "schedule_id": schedule_id,
                "status": str(publish_result.get("status", "published")),
                "external_post_id": str(publish_result.get("external_post_id", "")),
            }
        except Exception:
            failure = await workflow.execute_activity(
                handle_publish_failure,
                schedule_id,
                start_to_close_timeout=step_timeout,
            )
            return {
                "schedule_id": schedule_id,
                "status": str(failure.get("status", "failed")),
                "external_post_id": None,
            }
