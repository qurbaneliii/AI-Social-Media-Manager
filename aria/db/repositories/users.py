# filename: db/repositories/users.py
# purpose: Raw-SQL repository for users table lookup and creation.
# dependencies: asyncpg

from __future__ import annotations

from typing import Any

import asyncpg


def _to_dict(record: asyncpg.Record | None) -> dict[str, Any] | None:
    return dict(record) if record is not None else None


class UserRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_by_email(self, email: str, conn: asyncpg.Connection | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM users WHERE email = $1"
        if conn is not None:
            row = await conn.fetchrow(query, email)
            return _to_dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, email)
            return _to_dict(row)

    async def get_by_auth(
        self,
        auth_provider: str,
        auth_subject: str,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any] | None:
        query = "SELECT * FROM users WHERE auth_provider = $1 AND auth_subject = $2"
        if conn is not None:
            row = await conn.fetchrow(query, auth_provider, auth_subject)
            return _to_dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, auth_provider, auth_subject)
            return _to_dict(row)

    async def create(
        self,
        email: str,
        full_name: str,
        auth_provider: str,
        auth_subject: str,
        conn: asyncpg.Connection | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO users (email, full_name, auth_provider, auth_subject)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """
        if conn is not None:
            row = await conn.fetchrow(query, email, full_name, auth_provider, auth_subject)
            return dict(row)
        async with self.pool.acquire() as acq:
            row = await acq.fetchrow(query, email, full_name, auth_provider, auth_subject)
            return dict(row)
