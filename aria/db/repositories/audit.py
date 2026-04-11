# filename: db/repositories/audit.py
# purpose: Raw-SQL repository for append-only audit event writes and paginated reads.
# dependencies: asyncpg, json

from __future__ import annotations

import json
from typing import Any

import asyncpg


class AuditRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def log(
        self,
        company_id: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        actor_user_id: str | None = None,
        before_hash: str | None = None,
        after_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        INSERT INTO audit_events (
            company_id, actor_user_id, action, resource_type,
            resource_id, before_hash, after_hash, metadata
        )
        VALUES (
            $1::uuid,
            $2::uuid,
            $3,
            $4,
            $5::uuid,
            $6,
            $7,
            $8::jsonb
        )
        """
        args = (
            company_id,
            actor_user_id,
            action,
            resource_type,
            resource_id,
            before_hash,
            after_hash,
            json.dumps(metadata or {}),
        )
        if conn is not None:
            await conn.execute(query, *args)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, *args)

    async def get_by_company(
        self,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        query = """
        SELECT *
        FROM audit_events
        WHERE company_id = $1::uuid
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """
        if conn is not None:
            rows = await conn.fetch(query, company_id, limit, offset)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, company_id, limit, offset)
            return [dict(row) for row in rows]
