# filename: flows/posting.py
# purpose: Schedule/publish orchestration bridge between API, Redis dedupe, ingester, and Temporal workflows.
# dependencies: os, json, hashlib, datetime, asyncpg, redis.asyncio, temporalio.client, app.rules, app.tasks, db.repositories.schedules, memory.feedback

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

import asyncpg
import redis.asyncio as redis
from temporalio.client import Client

from app.rules import verify_webhook_signature
from app.tasks import run_weekly_reembedding
from db.connection import set_tenant
from db.repositories.schedules import ScheduleRepository
from memory.feedback import PerformanceIngester
from temporal.workflows.posting_workflow import PostingWorkflow


class PostingService:
    def __init__(self, pool: asyncpg.Pool, redis_client: redis.Redis, temporal_client: Client) -> None:
        self.pool = pool
        self.redis = redis_client
        self.temporal = temporal_client
        self.schedules = ScheduleRepository(pool)
        self.ingester = PerformanceIngester(pool)
        self.task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "aria-main")

    async def schedule_post(
        self,
        post_id: str,
        company_id: str,
        platform: str,
        run_at_utc: datetime,
        approval_mode: str,
    ) -> dict[str, str]:
        key_source = f"{post_id}:{platform}:{run_at_utc.isoformat()}"
        idempotency_key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                schedule = await self.schedules.create(
                    post_id=post_id,
                    company_id=company_id,
                    platform=platform,
                    run_at_utc=run_at_utc,
                    approval_mode=approval_mode,
                    idempotency_key=idempotency_key,
                    conn=conn,
                )
        schedule_id = str(schedule["schedule_id"])

        workflow_id = f"posting-{schedule_id}"
        await self.temporal.start_workflow(
            PostingWorkflow.run,
            schedule_id,
            id=workflow_id,
            task_queue=self.task_queue,
        )

        return {"schedule_id": schedule_id, "workflow_id": workflow_id}

    async def handle_webhook(self, raw_body: bytes, signature: str, platform: str) -> dict[str, bool]:
        secret = os.getenv(f"{platform.upper()}_WEBHOOK_SECRET", os.getenv("WEBHOOK_HMAC_SECRET", ""))
        if not secret:
            return {"accepted": False}
        if not verify_webhook_signature(raw_body, signature, secret):
            return {"accepted": False}

        body_hash = hashlib.sha256(raw_body).hexdigest()
        dedupe_key = f"webhook:{body_hash}"
        was_set = await self.redis.set(dedupe_key, "1", ex=600, nx=True)
        if not was_set:
            return {"accepted": False}

        payload = json.loads(raw_body.decode("utf-8"))
        await self.ingester.ingest_webhook(payload)

        company_id = str(payload.get("company_id", ""))
        if company_id:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await set_tenant(conn, company_id)
                    count_today = await conn.fetchval(
                        """
                        SELECT count(*)::int
                        FROM performance_metrics
                        WHERE company_id = $1::uuid
                          AND captured_at >= date_trunc('day', now())
                        """,
                        company_id,
                    )
            if int(count_today or 0) > 100:
                run_weekly_reembedding.delay(company_id)

        return {"accepted": True}
