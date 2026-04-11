# filename: memory/reembedder.py
# purpose: Batch re-embedding jobs for brand voice and archive corpus using OpenAI embeddings API.
# dependencies: os, json, logging, httpx, asyncpg

from __future__ import annotations

import json
import logging
import os
from typing import Any

import asyncpg
import httpx

from db.repositories.embeddings import EmbeddingRepository

logger = logging.getLogger(__name__)


class Reembedder:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.embedding_repo = EmbeddingRepository(pool)

    async def _embed_text_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        payload = {
            "model": "text-embedding-3-large",
            "input": texts,
        }
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"openai embedding failed: {response.status_code} {response.text}")

        data = response.json()
        return [list(map(float, row["embedding"])) for row in data["data"]]

    async def reembed_brand_voice(self, company_id: str) -> int:
        logger.info("reembed_brand_voice start company_id=%s", company_id)
        query = """
        SELECT p.post_id, pv.text
        FROM posts p
        JOIN post_variants pv ON pv.post_id = p.post_id AND pv.is_selected = TRUE
        WHERE p.company_id = $1::uuid
          AND p.status IN ('scheduled', 'published')
          AND p.created_at >= now() - interval '7 days'
        ORDER BY p.created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, company_id)
            profile_row = await conn.fetchrow(
                "SELECT profile_version FROM brand_profiles WHERE company_id = $1::uuid",
                company_id,
            )
            profile_version = int(profile_row["profile_version"] if profile_row else 1)

        total = 0
        batch_size = 50
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            texts = [str(r["text"]) for r in batch]
            embeddings = await self._embed_text_batch(texts)

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for record, embedding in zip(batch, embeddings):
                        await self.embedding_repo.insert_brand_voice(
                            company_id=company_id,
                            profile_version=profile_version,
                            text_chunk=str(record["text"]),
                            embedding=embedding,
                            metadata={"post_id": str(record["post_id"])},
                            conn=conn,
                        )
                        total += 1

            logger.info(
                "reembed_brand_voice progress company_id=%s processed=%s",
                company_id,
                total,
            )

        logger.info("reembed_brand_voice complete company_id=%s total=%s", company_id, total)
        return total

    async def reembed_corpus(self, company_id: str) -> int:
        logger.info("reembed_corpus start company_id=%s", company_id)
        query = """
        SELECT embedding_id, text_chunk
        FROM post_archive_embeddings
        WHERE company_id = $1::uuid
        ORDER BY created_at ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, company_id)

        total = 0
        batch_size = 50
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            texts = [str(r["text_chunk"]) for r in batch]
            embeddings = await self._embed_text_batch(texts)

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for record, embedding in zip(batch, embeddings):
                        await conn.execute(
                            """
                            UPDATE post_archive_embeddings
                            SET embedding = $2::vector,
                                created_at = now()
                            WHERE embedding_id = $1::uuid
                            """,
                            str(record["embedding_id"]),
                            "[" + ",".join(f"{float(v):.8f}" for v in embedding) + "]",
                        )
                        total += 1

            logger.info(
                "reembed_corpus progress company_id=%s processed=%s",
                company_id,
                total,
            )

        logger.info("reembed_corpus complete company_id=%s total=%s", company_id, total)
        return total
