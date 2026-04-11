# FILE: apps/scheduler/services/dead_letter_writer.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

import asyncpg


class DeadLetterWriter:
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool = db_pool

    async def process(self, schedule_id: UUID, company_id: UUID, payload: dict) -> dict:
        """Persist dead-letter schedule entry and produce dead-letter event payload."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO dead_letter_schedules (schedule_id, company_id, payload_json, created_at)
                VALUES ($1, $2, $3::jsonb, $4)
                """,
                schedule_id,
                company_id,
                json.dumps(payload),
                datetime.now(tz=timezone.utc),
            )
        return {
            "event_type": "post.publish.dead_letter.v1",
            "schedule_id": str(schedule_id),
            "company_id": str(company_id),
            "payload": payload,
        }
