# FILE: apps/audience-targeting/services/performance_signal_miner.py
from __future__ import annotations

from uuid import UUID

import asyncpg


class PerformanceSignalMiner:
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool = db_pool

    async def process(self, company_id: UUID) -> list[str]:
        """Compute top five audience segments by engagement delta above company mean."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH baseline AS (
                  SELECT COALESCE(avg(engagement_rate), 0) AS mean_eng
                  FROM performance_metrics
                  WHERE company_id = $1
                )
                SELECT COALESCE(attributes_json->>'audience_segment', 'unknown') AS segment,
                       avg(engagement_rate) - (SELECT mean_eng FROM baseline) AS delta
                FROM performance_metrics
                WHERE company_id = $1
                GROUP BY segment
                ORDER BY delta DESC
                LIMIT 5
                """,
                company_id,
            )
        return [str(r["segment"]) for r in rows]
