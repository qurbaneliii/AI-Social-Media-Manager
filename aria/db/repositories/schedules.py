# filename: db/repositories/schedules.py
# purpose: Raw-SQL repository for schedule queue lifecycle, due-run queries, and retry bookkeeping.
# dependencies: datetime, asyncpg

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg


class ScheduleRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        post_id: str,
        company_id: str,
        platform: str,
        run_at_utc: datetime,
        approval_mode: str,
        idempotency_key: str,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO schedules (
            post_id, company_id, platform, run_at_utc,
            status, approval_mode, idempotency_key
        )
        VALUES ($1::uuid, $2::uuid, $3, $4, 'queued', $5, $6)
        RETURNING *
        """
        args = (post_id, company_id, platform, run_at_utc, approval_mode, idempotency_key)
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return dict(row)

    async def update_status(
        self,
        schedule_id: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        UPDATE schedules
        SET status = $2,
            error_code = $3,
            error_message = $4
        WHERE schedule_id = $1::uuid
        """
        args = (schedule_id, status, error_code, error_message)
        if conn is not None:
            await conn.execute(query, *args)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, *args)

    async def get_due(
        self,
        before_utc: datetime,
        limit: int = 100,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        query = """
        SELECT *
        FROM schedules
        WHERE status = 'queued'
          AND run_at_utc <= $1
        ORDER BY run_at_utc ASC
        LIMIT $2
        """
        if conn is not None:
            rows = await conn.fetch(query, before_utc, limit)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, before_utc, limit)
            return [dict(row) for row in rows]

    async def record_retry(
        self,
        schedule_id: str,
        next_retry_at: datetime,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        UPDATE schedules
        SET retry_count = retry_count + 1,
            next_retry_at = $2
        WHERE schedule_id = $1::uuid
        """
        if conn is not None:
            await conn.execute(query, schedule_id, next_retry_at)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, schedule_id, next_retry_at)
