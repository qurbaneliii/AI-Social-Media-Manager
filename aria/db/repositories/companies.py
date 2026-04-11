# filename: db/repositories/companies.py
# purpose: Raw-SQL repository for companies table CRUD operations.
# dependencies: asyncpg, json

from __future__ import annotations

import json
from typing import Any

import asyncpg


def _to_dict(record: asyncpg.Record | None) -> dict[str, Any] | None:
    return dict(record) if record is not None else None


class CompanyRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_by_id(self, company_id: str, conn: asyncpg.Connection | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM companies WHERE company_id = $1"
        if conn is not None:
            row = await conn.fetchrow(query, company_id)
            return _to_dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, company_id)
            return _to_dict(row)

    async def create(
        self,
        name: str,
        industry_vertical: str,
        target_market: dict[str, Any],
        timezone: str,
        plan_tier: str,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO companies (name, industry_vertical, target_market, timezone, plan_tier)
        VALUES ($1, $2, $3::jsonb, $4, $5)
        RETURNING *
        """
        args = (name, industry_vertical, json.dumps(target_market), timezone, plan_tier)
        if conn is not None:
            row = await conn.fetchrow(query, *args)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *args)
            return dict(row)

    async def update(self, company_id: str, conn: asyncpg.Connection | None = None, **fields: Any) -> dict[str, Any]:
        if not fields:
            current = await self.get_by_id(company_id, conn=conn)
            if current is None:
                raise ValueError("Company not found")
            return current

        allowed = {"name", "industry_vertical", "target_market", "timezone", "plan_tier"}
        invalid = [key for key in fields if key not in allowed]
        if invalid:
            raise ValueError(f"Unsupported fields for update: {invalid}")

        parts: list[str] = []
        values: list[Any] = []
        idx = 1
        for key, value in fields.items():
            if key == "target_market":
                parts.append(f"{key} = ${idx}::jsonb")
                values.append(json.dumps(value))
            else:
                parts.append(f"{key} = ${idx}")
                values.append(value)
            idx += 1

        parts.append("updated_at = now()")
        values.append(company_id)
        query = f"UPDATE companies SET {', '.join(parts)} WHERE company_id = ${idx} RETURNING *"

        if conn is not None:
            row = await conn.fetchrow(query, *values)
            if row is None:
                raise ValueError("Company not found")
            return dict(row)

        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, *values)
            if row is None:
                raise ValueError("Company not found")
            return dict(row)
