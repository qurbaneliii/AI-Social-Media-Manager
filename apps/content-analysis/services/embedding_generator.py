# FILE: apps/content-analysis/services/embedding_generator.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import asyncpg
import numpy as np


class EmbeddingGenerator:
    def __init__(self, vector_db_pool: asyncpg.Pool) -> None:
        self.vector_db_pool = vector_db_pool

    async def process(self, company_id: UUID, embedding: np.ndarray, metadata_json: dict) -> int:
        """Persist a float32 768-dim vector into brand_voice_embeddings with metadata."""
        vector = embedding.astype(np.float32)
        if vector.shape[0] != 768:
            vector = np.resize(vector, 768).astype(np.float32)

        vector_literal = "[" + ",".join(f"{float(x):.8f}" for x in vector.tolist()) + "]"
        async with self.vector_db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO brand_voice_embeddings (company_id, embedding, metadata_json, created_at)
                VALUES ($1, $2::vector, $3::jsonb, $4)
                """,
                company_id,
                vector_literal,
                metadata_json,
                datetime.now(tz=timezone.utc),
            )
        return int(vector.shape[0])
