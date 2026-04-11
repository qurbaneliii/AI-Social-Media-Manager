# filename: app/cache.py
# purpose: Semantic cache backed by pgvector for similarity lookups and Redis for exact-match idempotency.
# dependencies: os, json, hashlib, uuid, datetime, httpx, asyncpg, redis.asyncio

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx
import redis.asyncio as redis


class SemanticCache:
    """Semantic + exact cache for prompt-response reuse."""

    def __init__(
        self,
        postgres_dsn: str,
        redis_url: str,
        openai_api_key: str,
        similarity_threshold: float = 0.92,
    ) -> None:
        self.postgres_dsn = postgres_dsn
        self.redis_url = redis_url
        self.openai_api_key = openai_api_key
        self.similarity_threshold = similarity_threshold
        self.pool: asyncpg.Pool | None = None
        self.redis_client: redis.Redis | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.postgres_dsn, min_size=1, max_size=10)
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await self._ensure_schema()

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
        if self.redis_client is not None:
            await self.redis_client.close()

    async def _ensure_schema(self) -> None:
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id UUID PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    embedding VECTOR(1536) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS semantic_cache_embedding_idx
                ON semantic_cache USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    async def _embed_prompt(self, prompt: str) -> list[float]:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for semantic cache embedding")

        payload = {
            "model": "text-embedding-3-small",
            "input": prompt,
        }
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"openai-embedding: HTTP {response.status_code} - {response.text}"
            )

        data = response.json()
        embedding = data["data"][0]["embedding"]
        if not isinstance(embedding, list) or len(embedding) != 1536:
            raise RuntimeError("openai-embedding: invalid embedding dimensions")
        return [float(x) for x in embedding]

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"

    async def get(self, request: str) -> str | None:
        if self.pool is None or self.redis_client is None:
            raise RuntimeError("SemanticCache not initialized")

        exact_key = self._hash_prompt(request)
        exact_hit = await self.redis_client.get(exact_key)
        if exact_hit is not None:
            return exact_hit

        embedding = await self._embed_prompt(request)
        vector_str = self._vector_literal(embedding)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT content, (1 - (embedding <=> $1::vector)) AS similarity
                FROM semantic_cache
                ORDER BY embedding <=> $1::vector
                LIMIT 1
                """,
                vector_str,
            )

        if row is None:
            return None

        similarity = float(row["similarity"])
        if similarity >= self.similarity_threshold:
            return str(row["content"])

        return None

    async def set(self, request: str, content: str) -> None:
        if self.pool is None or self.redis_client is None:
            raise RuntimeError("SemanticCache not initialized")

        embedding = await self._embed_prompt(request)
        vector_str = self._vector_literal(embedding)
        row_id = uuid.uuid4()

        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM semantic_cache WHERE created_at < $1",
                datetime.now(timezone.utc) - timedelta(hours=24),
            )
            await conn.execute(
                """
                INSERT INTO semantic_cache (id, prompt, embedding, content, created_at)
                VALUES ($1, $2, $3::vector, $4, NOW())
                """,
                row_id,
                request,
                vector_str,
                content,
            )

        exact_key = self._hash_prompt(request)
        await self.redis_client.set(exact_key, content, ex=300)


def build_cache_from_env() -> SemanticCache:
    """Factory helper for app startup wiring."""
    postgres_dsn = os.getenv("POSTGRES_DSN", "postgresql://aria:aria@postgres:5432/aria")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    return SemanticCache(
        postgres_dsn=postgres_dsn,
        redis_url=redis_url,
        openai_api_key=openai_api_key,
    )
