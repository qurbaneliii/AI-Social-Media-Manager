# FILE: apps/audience-targeting/services/baseline_builder.py
from __future__ import annotations

from uuid import UUID

import asyncpg


class BaselineBuilder:
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool = db_pool

    async def process(self, company_id: UUID) -> dict:
        """Load company target_market baseline from operational storage."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT target_market_json FROM companies WHERE id = $1", company_id)
        return dict(row["target_market_json"]) if row else {}
