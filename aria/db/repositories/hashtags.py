# filename: db/repositories/hashtags.py
# purpose: Raw-SQL repository for hashtag library upsert, usage tracking, ranking, and moderation flags.
# dependencies: asyncpg

from __future__ import annotations

from typing import Any

import asyncpg


class HashtagRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def upsert(
        self,
        company_id: str,
        platform: str,
        tag: str,
        tier: str,
        monthly_volume: int | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO hashtag_library (company_id, platform, tag, tier, monthly_volume)
        VALUES ($1::uuid, $2, $3, $4, $5)
        ON CONFLICT (company_id, platform, tag)
        DO UPDATE SET tier = EXCLUDED.tier,
                      monthly_volume = EXCLUDED.monthly_volume,
                      updated_at = now()
        RETURNING *
        """
        args = (company_id, platform, tag, tier, monthly_volume)
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return dict(row)

    async def increment_usage(
        self,
        company_id: str,
        platform: str,
        tag: str,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        UPDATE hashtag_library
        SET usage_count = usage_count + 1,
            updated_at = now()
        WHERE company_id = $1::uuid AND platform = $2 AND tag = $3
        """
        if conn is not None:
            await conn.execute(query, company_id, platform, tag)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, company_id, platform, tag)

    async def top_by_engagement(
        self,
        company_id: str,
        platform: str,
        limit: int = 50,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        query = """
        SELECT *
        FROM hashtag_library
        WHERE company_id = $1::uuid
          AND platform = $2
          AND banned = FALSE
        ORDER BY avg_engagement_lift DESC, recency_score DESC
        LIMIT $3
        """
        if conn is not None:
            rows = await conn.fetch(query, company_id, platform, limit)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, company_id, platform, limit)
            return [dict(row) for row in rows]

    async def mark_banned(
        self,
        company_id: str,
        platform: str,
        tag: str,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        query = """
        UPDATE hashtag_library
        SET banned = TRUE,
            updated_at = now()
        WHERE company_id = $1::uuid AND platform = $2 AND tag = $3
        """
        if conn is not None:
            await conn.execute(query, company_id, platform, tag)
            return
        async with self.pool.acquire() as acq:
            await acq.execute(query, company_id, platform, tag)
