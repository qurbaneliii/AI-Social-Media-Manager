# filename: db/connection.py
# purpose: asyncpg connection pool lifecycle and tenant/session context setup utilities.
# dependencies: os, asyncpg

from __future__ import annotations

import os

import asyncpg

_POOL: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Initialize singleton asyncpg pool."""
    global _POOL
    if _POOL is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")
        _POOL = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
    return _POOL


def get_pool() -> asyncpg.Pool:
    """Return initialized singleton pool."""
    if _POOL is None:
        raise RuntimeError("Database pool not initialized")
    return _POOL


async def close_pool() -> None:
    """Close and reset singleton pool."""
    global _POOL
    if _POOL is not None:
        await _POOL.close()
        _POOL = None


async def set_tenant(conn: asyncpg.Connection, company_id: str, role: str = "app") -> None:
    """Set tenant-scoped session variables for RLS policies."""
    safe_company_id = company_id.replace("'", "''")
    safe_role = role.replace("'", "''")
    await conn.execute(f"SET LOCAL app.company_id = '{safe_company_id}'")
    await conn.execute(f"SET LOCAL app.role = '{safe_role}'")
