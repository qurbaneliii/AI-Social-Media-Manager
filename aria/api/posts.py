# filename: api/posts.py
# purpose: Post generation API endpoints for dispatch and retrieval.
# dependencies: asyncpg, fastapi, pydantic, db.connection, db.repositories.posts, app.tasks

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.tasks import run_generation
from db.connection import set_tenant
from db.repositories.posts import PostRepository

router = APIRouter()


class GeneratePostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    intent: str
    core_message: str
    platform_targets: list[str] = Field(min_length=1)
    media_asset_id: str | None = None
    campaign_tag: str | None = None


@router.post("/generate")
async def generate_post(payload: GeneratePostRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    posts = PostRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, payload.company_id)
            post = await posts.create(
                company_id=payload.company_id,
                intent=payload.intent,
                core_message=payload.core_message,
                platform_targets=payload.platform_targets,
                created_by=None,
                campaign_tag=payload.campaign_tag,
                conn=conn,
            )
            post_id = str(post["post_id"])
            await posts.update_status(post_id, "generating", conn=conn)

    async_result = run_generation.delay(payload.company_id, post_id, payload.model_dump())
    return {
        "post_id": post_id,
        "task_id": async_result.id,
        "status": "generating",
    }


@router.get("/{post_id}")
async def get_post(post_id: str, company_id: str, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    posts = PostRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            post = await posts.get_by_id(post_id=post_id, conn=conn)
            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")
            variants = await conn.fetch(
                "SELECT * FROM post_variants WHERE post_id = $1::uuid ORDER BY variant_order ASC",
                post_id,
            )

    post["variants"] = [dict(v) for v in variants]
    return post
