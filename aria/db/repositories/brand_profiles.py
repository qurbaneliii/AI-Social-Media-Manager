# filename: db/repositories/brand_profiles.py
# purpose: Raw-SQL repository for brand_profiles table CRUD/update operations.
# dependencies: asyncpg, json

from __future__ import annotations

import json
from typing import Any

import asyncpg


class BrandProfileRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        company_id: str,
        brand_positioning_statement: str,
        tone_descriptors: list[str],
        tone_fingerprint_json: dict[str, Any],
        visual_style_json: dict[str, Any] | None = None,
        approved_vocabulary: list[str] | None = None,
        banned_vocabulary: list[str] | None = None,
        confidence: float | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO brand_profiles (
            company_id, brand_positioning_statement, tone_descriptors,
            tone_fingerprint_json, visual_style_json,
            approved_vocabulary, banned_vocabulary, confidence
        )
        VALUES (
            $1::uuid, $2, $3::text[],
            $4::jsonb, $5::jsonb,
            $6::text[], $7::text[], $8
        )
        RETURNING *
        """
        args = (
            company_id,
            brand_positioning_statement,
            tone_descriptors,
            json.dumps(tone_fingerprint_json),
            json.dumps(visual_style_json) if visual_style_json is not None else None,
            approved_vocabulary or [],
            banned_vocabulary or [],
            confidence,
        )
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return dict(row)

    async def get_by_company(
        self,
        company_id: str,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM brand_profiles WHERE company_id = $1::uuid"
        if conn is not None:
            row = await conn.fetchrow(query, company_id)
            return dict(row) if row else None
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, company_id)
            return dict(row) if row else None

    async def update_vocabulary(
        self,
        company_id: str,
        approved: list[str],
        banned: list[str],
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        UPDATE brand_profiles
        SET approved_vocabulary = $2::text[],
            banned_vocabulary = $3::text[],
            updated_at = now()
        WHERE company_id = $1::uuid
        RETURNING *
        """
        if conn is not None:
            row = await conn.fetchrow(query, company_id, approved, banned)
            if row is None:
                raise ValueError("brand_profile not found")
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, company_id, approved, banned)
            if row is None:
                raise ValueError("brand_profile not found")
            return dict(row)

    async def update_analysis(
        self,
        company_id: str,
        tone_fingerprint_json: dict[str, Any] | None = None,
        visual_style_json: dict[str, Any] | None = None,
        confidence: float | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        updates: list[str] = []
        args: list[Any] = [company_id]
        idx = 2

        if tone_fingerprint_json is not None:
            updates.append(f"tone_fingerprint_json = ${idx}::jsonb")
            args.append(json.dumps(tone_fingerprint_json))
            idx += 1

        if visual_style_json is not None:
            updates.append(f"visual_style_json = ${idx}::jsonb")
            args.append(json.dumps(visual_style_json))
            idx += 1

        if confidence is not None:
            updates.append(f"confidence = ${idx}")
            args.append(confidence)
            idx += 1

        updates.append("updated_at = now()")
        query = f"UPDATE brand_profiles SET {', '.join(updates)} WHERE company_id = $1::uuid RETURNING *"

        if conn is not None:
            row = await conn.fetchrow(query, *args)
            if row is None:
                raise ValueError("brand_profile not found")
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            if row is None:
                raise ValueError("brand_profile not found")
            return dict(row)
