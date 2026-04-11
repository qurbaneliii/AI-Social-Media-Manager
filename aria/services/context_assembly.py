# filename: services/context_assembly.py
# purpose: Fetch and shape generation context from brand, media, and embedding stores.
# dependencies: asyncpg, db.repositories.brand_profiles, db.repositories.embeddings

from __future__ import annotations

from typing import Any

import asyncpg

from db.connection import set_tenant
from db.repositories.brand_profiles import BrandProfileRepository
from db.repositories.embeddings import EmbeddingRepository


class ContextAssembler:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.brand_repo = BrandProfileRepository(pool)
        self.embedding_repo = EmbeddingRepository(pool)

    async def fetch_tone_profile(self, company_id: str) -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                profile = await self.brand_repo.get_by_company(company_id, conn=conn)
        if profile is None:
            return {
                "tone_descriptors": [],
                "tone_fingerprint_json": {},
                "approved_vocabulary": [],
                "banned_vocabulary": [],
            }
        return {
            "tone_descriptors": profile.get("tone_descriptors") or [],
            "tone_fingerprint_json": profile.get("tone_fingerprint_json") or {},
            "approved_vocabulary": profile.get("approved_vocabulary") or [],
            "banned_vocabulary": profile.get("banned_vocabulary") or [],
        }

    async def fetch_visual_profile(self, company_id: str, media_asset_id: str | None) -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                if media_asset_id is not None:
                    row = await conn.fetchrow(
                        "SELECT visual_analysis FROM media_assets WHERE asset_id = $1::uuid AND company_id = $2::uuid",
                        media_asset_id,
                        company_id,
                    )
                    if row and row["visual_analysis"] is not None:
                        return dict(row["visual_analysis"])

                profile = await conn.fetchrow(
                    "SELECT visual_style_json FROM brand_profiles WHERE company_id = $1::uuid",
                    company_id,
                )
                if profile and profile["visual_style_json"] is not None:
                    return dict(profile["visual_style_json"])

        return {}

    async def fetch_winner_examples(self, company_id: str, platforms: list[str], k: int = 8) -> list[dict[str, Any]]:
        query_embedding = [0.0] * 3072
        examples: list[dict[str, Any]] = []
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                for platform in platforms:
                    rows = await self.embedding_repo.search_post_archive(
                        company_id=company_id,
                        query_embedding=query_embedding,
                        platform=platform,
                        k=max(k * 3, 20),
                        conn=conn,
                    )
                    winners = [row for row in rows if float(row.get("performance_percentile") or 0.0) >= 80.0]
                    examples.extend(winners[:k])

        examples.sort(key=lambda row: float(row.get("similarity") or 0.0), reverse=True)
        return examples[:k]

    async def fetch_hashtag_priors(self, company_id: str, platforms: list[str], k: int = 50) -> list[dict[str, Any]]:
        query_embedding = [0.0] * 1536
        priors: list[dict[str, Any]] = []
        per_platform_k = max(1, k // max(len(platforms), 1))

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                for platform in platforms:
                    rows = await self.embedding_repo.search_hashtag(
                        company_id=company_id,
                        query_embedding=query_embedding,
                        platform=platform,
                        k=per_platform_k,
                        conn=conn,
                    )
                    priors.extend(rows)

        priors.sort(key=lambda row: float(row.get("weighted_score") or 0.0), reverse=True)
        return priors[:k]
