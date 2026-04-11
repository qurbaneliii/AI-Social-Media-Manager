# FILE: apps/hashtag-seo/services/vector_retriever.py
from __future__ import annotations

from uuid import UUID

import asyncpg


class VectorRetriever:
    def __init__(self, vector_db: asyncpg.Pool) -> None:
        self.vector_db = vector_db

    async def process(self, company_id: UUID, platform: str, probe_vector: list[float]) -> list[dict]:
        """Retrieve top 100 nearest hashtag vectors filtered by tenant/company and platform."""
        vector_literal = "[" + ",".join(f"{x:.8f}" for x in probe_vector[:768]) + "]"
        async with self.vector_db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT hashtag, performance_weight, metadata_json,
                       (1 - (embedding <=> $1::vector)) AS relevance
                FROM hashtag_embeddings
                WHERE company_id = $2 AND (metadata_json->>'platform') = $3
                ORDER BY embedding <=> $1::vector
                LIMIT 100
                """,
                vector_literal,
                company_id,
                platform,
            )
        return [dict(r) for r in rows]
