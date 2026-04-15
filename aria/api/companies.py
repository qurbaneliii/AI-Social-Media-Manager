# filename: api/companies.py
# purpose: Company-scoped post listing endpoint under v1 contract.
# dependencies: asyncpg, fastapi, db.connection, db.repositories.posts

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, Request

from db.connection import set_tenant
from db.repositories.posts import PostRepository

router = APIRouter()


@router.get("/{company_id}/posts")
async def list_company_posts(
    company_id: str,
    request: Request,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    repo = PostRepository(pool)

    if limit is not None or offset is not None:
        safe_page_size = max(min(limit or 20, 100), 1)
        safe_offset = max(offset or 0, 0)
        safe_page = (safe_offset // safe_page_size) + 1
    else:
        safe_page = max(page or 1, 1)
        safe_page_size = max(min(page_size or 20, 100), 1)
        safe_offset = (safe_page - 1) * safe_page_size

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            items = await repo.list_by_company(
                company_id=company_id,
                status=status,
                limit=safe_page_size,
                offset=safe_offset,
                conn=conn,
            )

    return {
        "items": items,
        "page": safe_page,
        "page_size": safe_page_size,
        "limit": safe_page_size,
        "offset": safe_offset,
        "count": len(items),
    }
