# filename: app/main.py
# purpose: FastAPI entrypoint exposing generation, memory ingestion, repository-backed retrieval, and router diagnostics endpoints.
# dependencies: json, logging, contextlib, fastapi, celery.result, app/models, app/cache, app/router, app/tasks, db modules

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import boto3
import redis.asyncio as redis
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client as TemporalClient

from api import (
    analytics_router,
    companies_router,
    llm_proxy_router,
    media_router,
    oauth_router,
    onboarding_router,
    posts_router,
    schedules_router,
    webhooks_router,
)
from app.cache import SemanticCache, build_cache_from_env
from app.models import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    EmbeddingSearchRequest,
    EmbeddingSearchResponse,
    PostListResponse,
    PostDetailResponse,
    AuditListResponse,
    QueuedResponse,
    RouterStatusItem,
    RouterStatusResponse,
    TaskStatusResponse,
)
from app.router import LLMRouter, build_default_router
from app.tasks import (
    calibrate_tone,
    celery,
    generate_audience,
    generate_caption,
    generate_hashtags,
    generate_seo_metadata,
    ingest_performance_webhook,
)
from db.connection import close_pool, init_pool, set_tenant
from db.repositories.audit import AuditRepository
from db.repositories.embeddings import EmbeddingRepository
from db.repositories.posts import PostRepository
from flows.posting import PostingService
from services.media import MediaService
from services.oauth import OAuthService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        parsed = [origin.strip() for origin in raw.split(",") if origin.strip()]
        if parsed:
            return parsed
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache: SemanticCache = build_cache_from_env()
    await cache.connect()
    llm_router: LLMRouter = build_default_router()
    pool = await init_pool()
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    temporal_client = await TemporalClient.connect(
        os.getenv("TEMPORAL_HOST", "localhost:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
    )

    s3_client = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        region_name=os.getenv("MINIO_REGION", "us-east-1"),
    )

    app.state.semantic_cache = cache
    app.state.llm_router = llm_router
    app.state.db_pool = pool
    app.state.redis = redis_client
    app.state.temporal_client = temporal_client
    app.state.s3_client = s3_client
    app.state.post_repo = PostRepository(pool)
    app.state.embedding_repo = EmbeddingRepository(pool)
    app.state.audit_repo = AuditRepository(pool)
    app.state.media_service = MediaService(pool, s3_client)
    app.state.oauth_service = OAuthService(pool, redis_client)
    app.state.posting_service = PostingService(pool, redis_client, temporal_client)

    logger.info("startup_complete")
    try:
        yield
    finally:
        await cache.close()
        await redis_client.aclose()
        await close_pool()
        logger.info("shutdown_complete")


app = FastAPI(title="ARIA API and Tooling Plan", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(onboarding_router, prefix="/v1/onboarding", tags=["onboarding"])
app.include_router(posts_router, prefix="/v1/posts", tags=["posts"])
app.include_router(schedules_router, prefix="/v1/schedules", tags=["schedules"])
app.include_router(webhooks_router, prefix="/v1/webhooks", tags=["webhooks"])
app.include_router(companies_router, prefix="/v1/companies", tags=["companies"])
app.include_router(analytics_router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(llm_proxy_router, prefix="/v1/llm/proxy", tags=["llm-proxy"])
app.include_router(media_router, prefix="/v1/media", tags=["media"])
app.include_router(oauth_router, prefix="/v1/oauth", tags=["oauth"])


def _build_cache_key(request: GenerateRequest) -> str:
    return json.dumps(
        {
            "tenant_id": request.tenant_id,
            "module": request.module,
            "payload": request.payload,
        },
        sort_keys=True,
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    cache_key = _build_cache_key(request)
    cache: SemanticCache = app.state.semantic_cache

    cached_content = await cache.get(cache_key)
    if cached_content is not None:
        return GenerateResponse(cached=True, result=json.loads(cached_content))

    task_map = {
        "generate_caption": generate_caption,
        "generate_hashtags": generate_hashtags,
        "generate_audience": generate_audience,
        "generate_seo_metadata": generate_seo_metadata,
        "calibrate_tone": calibrate_tone,
    }
    task_fn = task_map.get(request.module)
    if task_fn is None:
        raise HTTPException(status_code=400, detail="Unsupported generation module")

    async_result = task_fn.delay(request.tenant_id, request.payload)
    return GenerateResponse(cached=False, task_id=async_result.id)


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    task_result = AsyncResult(task_id, app=celery)

    if task_result.state == "PENDING":
        return TaskStatusResponse(task_id=task_id, status="PENDING")

    if task_result.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="FAILURE",
            error=str(task_result.result),
        )

    if task_result.state == "SUCCESS":
        result = task_result.result
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="Unexpected task payload type")
        return TaskStatusResponse(task_id=task_id, status="SUCCESS", result=result)

    return TaskStatusResponse(task_id=task_id, status=task_result.state)


@app.get("/router/status", response_model=RouterStatusResponse)
async def router_status() -> RouterStatusResponse:
    router: LLMRouter = app.state.llm_router
    status = router.get_status()
    return RouterStatusResponse(
        providers={
            name: RouterStatusItem(**details) for name, details in status.items()
        }
    )


@app.post("/metrics/webhook", response_model=QueuedResponse)
async def metrics_webhook(payload: dict[str, Any]) -> QueuedResponse:
    ingest_performance_webhook.delay(payload)
    return QueuedResponse(queued=True)


@app.get("/companies/{company_id}/posts", response_model=PostListResponse)
async def company_posts(
    company_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PostListResponse:
    post_repo: PostRepository = app.state.post_repo
    pool: asyncpg.Pool = app.state.db_pool

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            items = await post_repo.list_by_company(
                company_id=company_id,
                status=status,
                limit=limit,
                offset=offset,
                conn=conn,
            )
    return PostListResponse(items=items, limit=limit, offset=offset)


@app.get("/posts/{post_id}", response_model=PostDetailResponse)
async def post_detail(post_id: str, company_id: str) -> PostDetailResponse:
    post_repo: PostRepository = app.state.post_repo
    pool: asyncpg.Pool = app.state.db_pool

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            item = await post_repo.get_by_id(post_id=post_id, conn=conn)
    return PostDetailResponse(item=item)


@app.post("/embeddings/search", response_model=EmbeddingSearchResponse)
async def embeddings_search(request: EmbeddingSearchRequest) -> EmbeddingSearchResponse:
    embedding_repo: EmbeddingRepository = app.state.embedding_repo
    pool: asyncpg.Pool = app.state.db_pool

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, request.company_id)
            if request.table == "brand_voice_embeddings":
                items = await embedding_repo.search_brand_voice(
                    company_id=request.company_id,
                    query_embedding=request.query_embedding,
                    k=request.k,
                    conn=conn,
                )
            elif request.table == "hashtag_embeddings":
                items = await embedding_repo.search_hashtag(
                    company_id=request.company_id,
                    query_embedding=request.query_embedding,
                    k=request.k,
                    platform=request.filters.get("platform"),
                    conn=conn,
                )
            elif request.table == "post_archive_embeddings":
                items = await embedding_repo.search_post_archive(
                    company_id=request.company_id,
                    query_embedding=request.query_embedding,
                    k=request.k,
                    platform=request.filters.get("platform"),
                    intent=request.filters.get("intent"),
                    conn=conn,
                )
            elif request.table == "audience_profile_embeddings":
                items = await embedding_repo.search_audience_profile(
                    company_id=request.company_id,
                    query_embedding=request.query_embedding,
                    k=request.k,
                    platform=request.filters.get("platform"),
                    conn=conn,
                )
            else:
                raise HTTPException(status_code=400, detail="Unsupported embedding table")

    return EmbeddingSearchResponse(items=items)


@app.get("/audit/{company_id}", response_model=AuditListResponse)
async def audit_by_company(company_id: str, limit: int = 100, offset: int = 0) -> AuditListResponse:
    audit_repo: AuditRepository = app.state.audit_repo
    pool: asyncpg.Pool = app.state.db_pool

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, company_id)
            items = await audit_repo.get_by_company(
                company_id=company_id,
                limit=limit,
                offset=offset,
                conn=conn,
            )
    return AuditListResponse(items=items, limit=limit, offset=offset)
