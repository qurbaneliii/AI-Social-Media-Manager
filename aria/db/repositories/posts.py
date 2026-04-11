# filename: db/repositories/posts.py
# purpose: Raw-SQL repository for posts lifecycle and listing operations.
# dependencies: asyncpg, json

from __future__ import annotations

import json
from typing import Any

import asyncpg


def _to_dict(record: asyncpg.Record | None) -> dict[str, Any] | None:
    return dict(record) if record is not None else None


class PostRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        company_id: str,
        intent: str,
        core_message: str,
        platform_targets: list[str],
        created_by: str | None,
        campaign_tag: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO posts (company_id, intent, core_message, campaign_tag, status, platform_targets, created_by)
        VALUES ($1::uuid, $2, $3, $4, 'draft', $5::text[], $6::uuid)
        RETURNING *
        """
        args = (company_id, intent, core_message, campaign_tag, platform_targets, created_by)
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return dict(row)

    async def update_status(self, post_id: str, status: str, conn: asyncpg.Connection | None = None) -> None:
        query = "UPDATE posts SET status = $2, updated_at = now() WHERE post_id = $1::uuid"
        if conn is not None:
            await conn.execute(query, post_id, status)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, post_id, status)

    async def attach_generated_package(
        self,
        post_id: str,
        generated_package_json: dict[str, Any],
        quality_score: float,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        UPDATE posts
        SET generated_package_json = $2::jsonb,
            quality_score = $3,
            status = 'generated',
            updated_at = now()
        WHERE post_id = $1::uuid
        """
        args = (post_id, json.dumps(generated_package_json), quality_score)
        if conn is not None:
            await conn.execute(query, *args)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, *args)

    async def list_by_company(
        self,
        company_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        if status is None:
            query = """
            SELECT *
            FROM posts
            WHERE company_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """
            args = (company_id, limit, offset)
        else:
            query = """
            SELECT *
            FROM posts
            WHERE company_id = $1::uuid AND status = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """
            args = (company_id, status, limit, offset)

        if conn is not None:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, *args)
            return [dict(row) for row in rows]

    async def get_by_id(self, post_id: str, conn: asyncpg.Connection | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM posts WHERE post_id = $1::uuid"
        if conn is not None:
            row = await conn.fetchrow(query, post_id)
            return _to_dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, post_id)
            return _to_dict(row)
