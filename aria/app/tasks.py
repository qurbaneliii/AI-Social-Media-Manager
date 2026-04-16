# filename: app/tasks.py
# purpose: Celery generation and memory tasks with schema validation, retries, and periodic scheduling.
# dependencies: os, json, asyncio, datetime, celery, asyncpg, pydantic, app.router, app.providers, app.cache, memory modules

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import asyncpg
from celery import Celery
from celery.schedules import crontab
from pydantic import BaseModel, ConfigDict, Field

from app.cache import build_cache_from_env
from app.providers import ProviderError
from app.router import build_default_router
from memory.feedback import PerformanceIngester
from memory.reembedder import Reembedder

celery = Celery(
    "aria",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "weekly-reembedding": {
            "task": "run_weekly_reembedding",
            "schedule": crontab(minute=0, hour=2, day_of_week=1),
            "args": (os.getenv("DEFAULT_COMPANY_ID", "00000000-0000-0000-0000-000000000000"),),
        },
        "monthly-corpus-reembedding": {
            "task": "run_monthly_corpus_reembedding",
            "schedule": crontab(minute=0, hour=3, day_of_month=1),
            "args": (os.getenv("DEFAULT_COMPANY_ID", "00000000-0000-0000-0000-000000000000"),),
        },
    },
)


CAPTION_PROMPT_TEMPLATE = (
    "Generate JSON with keys caption,tone for company='{company}', intent='{intent}', "
    "topic='{topic}', platform='{platform}'."
)
HASHTAG_PROMPT_TEMPLATE = (
    "Generate JSON with key hashtags (list of strings) for topic='{topic}' and platform='{platform}'."
)
AUDIENCE_PROMPT_TEMPLATE = (
    "Generate JSON with keys segments (list of strings), confidence (0..1) "
    "for profile_hash='{profile_hash}', topic='{topic}'."
)
SEO_PROMPT_TEMPLATE = (
    "Generate JSON with keys title,description,keywords (list of strings) for caption_hash='{caption_hash}'."
)
TONE_PROMPT_TEMPLATE = (
    "Generate JSON with keys tone_score (0..1), suggested_tone for brand_profile='{brand_profile}' and content='{content}'."
)


class CaptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    platform: str = Field(min_length=1)


class CaptionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str
    tone: str


class HashtagInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1)
    platform: str = Field(min_length=1)


class HashtagOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hashtags: list[str]


class AudienceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_hash: str = Field(min_length=1)
    topic: str = Field(min_length=1)


class AudienceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class SEOInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption_hash: str = Field(min_length=1)


class SEOOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    keywords: list[str]


class ToneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_profile: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ToneOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone_score: float = Field(ge=0.0, le=1.0)
    suggested_tone: str


class WebhookIngestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    post_id: str | None = None
    platform: str
    external_post_id: str | None = None
    impressions: int = Field(ge=0)
    reach: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0)
    click_through_rate: float = Field(ge=0.0)
    saves: int = Field(ge=0)
    shares: int = Field(ge=0)
    follower_growth_delta: int = 0
    posting_timestamp: str
    captured_at: str


async def _run_router_generate(tenant_id: str, prompt: str, max_tokens: int) -> str:
    router = build_default_router()
    return await router.generate(tenant_id=tenant_id, prompt=prompt, max_tokens=max_tokens)


async def _cache_result(prompt: str, result: dict[str, Any]) -> None:
    cache = build_cache_from_env()
    await cache.connect()
    try:
        await cache.set(prompt, json.dumps(result, separators=(",", ":")))
    finally:
        await cache.close()


async def _run_ingest_webhook(payload: dict[str, Any]) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    try:
        ingester = PerformanceIngester(pool)
        await ingester.ingest_webhook(payload)
    finally:
        await pool.close()


async def _run_weekly_reembedding(company_id: str) -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    try:
        reembedder = Reembedder(pool)
        return await reembedder.reembed_brand_voice(company_id)
    finally:
        await pool.close()


async def _run_monthly_reembedding(company_id: str) -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    try:
        reembedder = Reembedder(pool)
        return await reembedder.reembed_corpus(company_id)
    finally:
        await pool.close()


async def _run_generation_flow(company_id: str, post_id: str, request: dict[str, Any]) -> dict[str, Any]:
    from flows.generation import GenerationOrchestrator

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    try:
        orchestrator = GenerationOrchestrator(pool)
        return await orchestrator.run(company_id=company_id, post_id=post_id, request=request)
    finally:
        await pool.close()


async def _run_onboarding_quality_check(company_id: str) -> dict[str, Any]:
    from flows.onboarding import OnboardingOrchestrator

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    try:
        orchestrator = OnboardingOrchestrator(pool)
        return await orchestrator.run_quality_check(company_id)
    finally:
        await pool.close()


def _retry_with_backoff(task: Any, exc: Exception) -> None:
    retries = int(getattr(task.request, "retries", 0))
    delay_seconds = 2 * (2**retries)
    raise task.retry(exc=exc, countdown=delay_seconds, max_retries=3)


def _parse_and_validate(raw: str, output_model: type[BaseModel]) -> dict[str, Any]:
    payload = json.loads(raw)
    validated = output_model.model_validate(payload)
    return validated.model_dump()


def _build_cache_key(tenant_id: str, module: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "tenant_id": tenant_id,
            "module": module,
            "payload": payload,
        },
        sort_keys=True,
    )


def _sanitize_prompt_value(value: str, max_chars: int) -> str:
    compact = " ".join(value.replace("\x00", " ").split()).strip()
    return compact[:max_chars]


@celery.task(bind=True, name="generate_caption")
def generate_caption(self: Any, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = CaptionInput.model_validate(payload)
    prompt = CAPTION_PROMPT_TEMPLATE.format(
        company=_sanitize_prompt_value(data.company, 200),
        intent=_sanitize_prompt_value(data.intent, 120),
        topic=_sanitize_prompt_value(data.topic, 2000),
        platform=_sanitize_prompt_value(data.platform, 50),
    )

    try:
        raw = asyncio.run(_run_router_generate(tenant_id, prompt, max_tokens=700))
    except ProviderError as exc:
        _retry_with_backoff(self, exc)

    result = _parse_and_validate(raw, CaptionOutput)
    try:
        cache_key = _build_cache_key(tenant_id, "generate_caption", payload)
        asyncio.run(_cache_result(cache_key, result))
    except Exception:
        pass
    return result


@celery.task(bind=True, name="generate_hashtags")
def generate_hashtags(self: Any, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = HashtagInput.model_validate(payload)
    prompt = HASHTAG_PROMPT_TEMPLATE.format(
        topic=_sanitize_prompt_value(data.topic, 2000),
        platform=_sanitize_prompt_value(data.platform, 50),
    )

    try:
        raw = asyncio.run(_run_router_generate(tenant_id, prompt, max_tokens=300))
    except ProviderError as exc:
        _retry_with_backoff(self, exc)

    result = _parse_and_validate(raw, HashtagOutput)
    try:
        cache_key = _build_cache_key(tenant_id, "generate_hashtags", payload)
        asyncio.run(_cache_result(cache_key, result))
    except Exception:
        pass
    return result


@celery.task(bind=True, name="generate_audience")
def generate_audience(self: Any, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = AudienceInput.model_validate(payload)
    prompt = AUDIENCE_PROMPT_TEMPLATE.format(
        profile_hash=_sanitize_prompt_value(data.profile_hash, 200),
        topic=_sanitize_prompt_value(data.topic, 2000),
    )

    try:
        raw = asyncio.run(_run_router_generate(tenant_id, prompt, max_tokens=500))
    except ProviderError as exc:
        _retry_with_backoff(self, exc)

    result = _parse_and_validate(raw, AudienceOutput)
    try:
        cache_key = _build_cache_key(tenant_id, "generate_audience", payload)
        asyncio.run(_cache_result(cache_key, result))
    except Exception:
        pass
    return result


@celery.task(bind=True, name="generate_seo_metadata")
def generate_seo_metadata(self: Any, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = SEOInput.model_validate(payload)
    prompt = SEO_PROMPT_TEMPLATE.format(caption_hash=_sanitize_prompt_value(data.caption_hash, 200))

    try:
        raw = asyncio.run(_run_router_generate(tenant_id, prompt, max_tokens=350))
    except ProviderError as exc:
        _retry_with_backoff(self, exc)

    result = _parse_and_validate(raw, SEOOutput)
    try:
        cache_key = _build_cache_key(tenant_id, "generate_seo_metadata", payload)
        asyncio.run(_cache_result(cache_key, result))
    except Exception:
        pass
    return result


@celery.task(bind=True, name="calibrate_tone")
def calibrate_tone(self: Any, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = ToneInput.model_validate(payload)
    prompt = TONE_PROMPT_TEMPLATE.format(
        brand_profile=_sanitize_prompt_value(data.brand_profile, 500),
        content=_sanitize_prompt_value(data.content, 3000),
    )

    try:
        raw = asyncio.run(_run_router_generate(tenant_id, prompt, max_tokens=450))
    except ProviderError as exc:
        _retry_with_backoff(self, exc)

    result = _parse_and_validate(raw, ToneOutput)
    try:
        cache_key = _build_cache_key(tenant_id, "calibrate_tone", payload)
        asyncio.run(_cache_result(cache_key, result))
    except Exception:
        pass
    return result


@celery.task(bind=True, name="ingest_performance_webhook")
def ingest_performance_webhook(self: Any, payload: dict[str, Any]) -> None:
    data = WebhookIngestInput.model_validate(payload)
    asyncio.run(_run_ingest_webhook(data.model_dump()))


@celery.task(bind=True, name="run_weekly_reembedding")
def run_weekly_reembedding(self: Any, company_id: str) -> dict[str, int]:
    total = asyncio.run(_run_weekly_reembedding(company_id))
    return {"reembedded": int(total)}


@celery.task(bind=True, name="run_monthly_corpus_reembedding")
def run_monthly_corpus_reembedding(self: Any, company_id: str) -> dict[str, int]:
    total = asyncio.run(_run_monthly_reembedding(company_id))
    return {"reembedded": int(total)}


@celery.task(bind=True, name="run_generation")
def run_generation(self: Any, company_id: str, post_id: str, request: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(_run_generation_flow(company_id=company_id, post_id=post_id, request=request))


@celery.task(bind=True, name="run_onboarding_quality_check")
def run_onboarding_quality_check(self: Any, company_id: str) -> dict[str, Any]:
    return asyncio.run(_run_onboarding_quality_check(company_id=company_id))
