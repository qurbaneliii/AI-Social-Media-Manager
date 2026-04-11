# filename: db/repositories/embeddings.py
# purpose: Raw-SQL repository for vector insert/search across all embedding collections.
# dependencies: asyncpg, json, uuid

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


class EmbeddingRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def insert_brand_voice(
        self,
        company_id: str,
        profile_version: int,
        text_chunk: str,
        embedding: list[float],
        metadata: dict[str, Any],
        language: str = "en",
        conn: asyncpg.Connection | None = None,
    ) -> str:
        vector = _vector_literal(embedding)
        existing_query = """
        SELECT embedding_id
        FROM brand_voice_embeddings
        WHERE company_id = $1::uuid AND profile_version = $2 AND text_chunk = $3
        LIMIT 1
        """
        insert_query = """
        INSERT INTO brand_voice_embeddings (
            embedding_id, company_id, profile_version, text_chunk, embedding, language, metadata
        ) VALUES ($1::uuid, $2::uuid, $3, $4, $5::vector, $6, $7::jsonb)
        """
        update_query = """
        UPDATE brand_voice_embeddings
        SET embedding = $2::vector,
            language = $3,
            metadata = $4::jsonb,
            created_at = now()
        WHERE embedding_id = $1::uuid
        """

        async def _run(c: asyncpg.Connection) -> str:
            row = await c.fetchrow(existing_query, company_id, profile_version, text_chunk)
            if row is None:
                embedding_id = str(uuid.uuid4())
                await c.execute(
                    insert_query,
                    embedding_id,
                    company_id,
                    profile_version,
                    text_chunk,
                    vector,
                    language,
                    json.dumps(metadata),
                )
                return embedding_id

            embedding_id = str(row["embedding_id"])
            await c.execute(update_query, embedding_id, vector, language, json.dumps(metadata))
            return embedding_id

        if conn is not None:
            return await _run(conn)
        async with self.pool.acquire() as acq:
            return await _run(acq)

    async def search_brand_voice(
        self,
        company_id: str,
        query_embedding: list[float],
        k: int,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        vector = _vector_literal(query_embedding)
        query = """
        SELECT *, (1 - (embedding <=> $2::vector)) AS similarity
        FROM brand_voice_embeddings
        WHERE company_id = $1::uuid
        ORDER BY embedding <=> $2::vector
        LIMIT $3
        """
        if conn is not None:
            rows = await conn.fetch(query, company_id, vector, k)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, company_id, vector, k)
            return [dict(row) for row in rows]

    async def insert_hashtag(
        self,
        company_id: str,
        platform: str,
        hashtag: str,
        context_text: str,
        embedding: list[float],
        metadata: dict[str, Any],
        engagement_lift: float = 0.0,
        recency_score: float = 0.0,
        conn: asyncpg.Connection | None = None,
    ) -> str:
        query = """
        INSERT INTO hashtag_embeddings (
            embedding_id, company_id, platform, hashtag, context_text,
            embedding, engagement_lift, recency_score, metadata
        ) VALUES (
            $1::uuid, $2::uuid, $3, $4, $5,
            $6::vector, $7, $8, $9::jsonb
        )
        RETURNING embedding_id
        """
        embedding_id = str(uuid.uuid4())
        args = (
            embedding_id,
            company_id,
            platform,
            hashtag,
            context_text,
            _vector_literal(embedding),
            engagement_lift,
            recency_score,
            json.dumps(metadata),
        )
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return str(row["embedding_id"])
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return str(row["embedding_id"])

    async def search_hashtag(
        self,
        company_id: str,
        query_embedding: list[float],
        k: int,
        platform: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        vector = _vector_literal(query_embedding)
        if platform is None:
            query = """
            SELECT *,
                   (1 - (embedding <=> $2::vector)) AS similarity,
                   (0.6 * (1 - (embedding <=> $2::vector))
                    + 0.25 * engagement_lift
                    + 0.15 * recency_score) AS weighted_score
            FROM hashtag_embeddings
            WHERE company_id = $1::uuid
            ORDER BY weighted_score DESC
            LIMIT $3
            """
            args = (company_id, vector, k)
        else:
            query = """
            SELECT *,
                   (1 - (embedding <=> $2::vector)) AS similarity,
                   (0.6 * (1 - (embedding <=> $2::vector))
                    + 0.25 * engagement_lift
                    + 0.15 * recency_score) AS weighted_score
            FROM hashtag_embeddings
            WHERE company_id = $1::uuid AND platform = $3
            ORDER BY weighted_score DESC
            LIMIT $4
            """
            args = (company_id, vector, platform, k)

        if conn is not None:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, *args)
            return [dict(row) for row in rows]

    async def insert_post_archive(
        self,
        company_id: str,
        post_id: str | None,
        platform: str,
        intent: str,
        text_chunk: str,
        embedding: list[float],
        metadata: dict[str, Any],
        performance_percentile: float | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> str:
        query = """
        INSERT INTO post_archive_embeddings (
            embedding_id, company_id, post_id, platform, intent,
            text_chunk, embedding, performance_percentile, metadata
        ) VALUES (
            $1::uuid, $2::uuid, $3::uuid, $4, $5,
            $6, $7::vector, $8, $9::jsonb
        )
        RETURNING embedding_id
        """
        embedding_id = str(uuid.uuid4())
        args = (
            embedding_id,
            company_id,
            post_id,
            platform,
            intent,
            text_chunk,
            _vector_literal(embedding),
            performance_percentile,
            json.dumps(metadata),
        )
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return str(row["embedding_id"])
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return str(row["embedding_id"])

    async def search_post_archive(
        self,
        company_id: str,
        query_embedding: list[float],
        k: int,
        platform: str | None = None,
        intent: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        vector = _vector_literal(query_embedding)

        where_clauses = ["company_id = $1::uuid"]
        args: list[Any] = [company_id, vector]
        idx = 3

        if platform is not None:
            where_clauses.append(f"platform = ${idx}")
            args.append(platform)
            idx += 1

        if intent is not None:
            where_clauses.append(f"intent = ${idx}")
            args.append(intent)
            idx += 1

        limit_placeholder = f"${idx}"
        args.append(k)

        query = f"""
        SELECT *, (1 - (embedding <=> $2::vector)) AS similarity
        FROM post_archive_embeddings
        WHERE {' AND '.join(where_clauses)}
        ORDER BY embedding <=> $2::vector
        LIMIT {limit_placeholder}
        """

        if conn is not None:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, *args)
            return [dict(row) for row in rows]

    async def insert_audience_profile(
        self,
        company_id: str,
        platform: str,
        segment_label: str,
        summary_text: str,
        embedding: list[float],
        metadata: dict[str, Any],
        segment_performance: float | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> str:
        query = """
        INSERT INTO audience_profile_embeddings (
            embedding_id, company_id, platform, segment_label, summary_text,
            embedding, segment_performance, metadata
        ) VALUES (
            $1::uuid, $2::uuid, $3, $4, $5,
            $6::vector, $7, $8::jsonb
        )
        RETURNING embedding_id
        """
        embedding_id = str(uuid.uuid4())
        args = (
            embedding_id,
            company_id,
            platform,
            segment_label,
            summary_text,
            _vector_literal(embedding),
            segment_performance,
            json.dumps(metadata),
        )
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return str(row["embedding_id"])
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return str(row["embedding_id"])

    async def search_audience_profile(
        self,
        company_id: str,
        query_embedding: list[float],
        k: int,
        platform: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> list[dict[str, Any]]:
        vector = _vector_literal(query_embedding)
        if platform is None:
            query = """
            SELECT *, (1 - (embedding <=> $2::vector)) AS similarity
            FROM audience_profile_embeddings
            WHERE company_id = $1::uuid
            ORDER BY embedding <=> $2::vector
            LIMIT $3
            """
            args = (company_id, vector, k)
        else:
            query = """
            SELECT *, (1 - (embedding <=> $2::vector)) AS similarity
            FROM audience_profile_embeddings
            WHERE company_id = $1::uuid
              AND platform = $3
            ORDER BY embedding <=> $2::vector
            LIMIT $4
            """
            args = (company_id, vector, platform, k)

        if conn is not None:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        async with self.pool.acquire() as acq:
            rows = await acq.fetch(query, *args)
            return [dict(row) for row in rows]
