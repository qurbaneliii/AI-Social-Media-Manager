# FILE: apps/hashtag-seo/tests/test_services.py
from __future__ import annotations

import pytest

from config import Settings
from services.tier_allocator import TierAllocator
from services.seo_metadata_generator import SeoMetadataGenerator


@pytest.mark.asyncio
async def test_tier_quota_enforcement() -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgres://x",
            "REDIS_URL": "redis://x",
            "S3_BUCKET": "b",
            "LLM_PROXY_URL": "http://x",
            "SERVICE_NAME": "s",
            "SERVICE_VERSION": "1.0.0",
            "OTLP_ENDPOINT": "http://x",
            "LOG_LEVEL": "INFO",
            "AWS_REGION": "us-east-1",
            "KMS_KEY_ID": "k",
        }
    )
    allocator = TierAllocator(settings)
    scored = [{"token": f"a{i}", "score": 1 - i * 0.01, "search_volume": 600000} for i in range(20)]
    out = await allocator.process(scored)
    assert len(out) == settings.broad_quota + settings.niche_quota + settings.micro_quota


@pytest.mark.asyncio
async def test_seo_metadata_limits() -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgres://x",
            "REDIS_URL": "redis://x",
            "S3_BUCKET": "b",
            "LLM_PROXY_URL": "http://x",
            "SERVICE_NAME": "s",
            "SERVICE_VERSION": "1.0.0",
            "OTLP_ENDPOINT": "http://x",
            "LOG_LEVEL": "INFO",
            "AWS_REGION": "us-east-1",
            "KMS_KEY_ID": "k",
        }
    )
    seo = await SeoMetadataGenerator(settings).process("hello world " * 20, ["alpha"])
    assert len(seo["meta_title"]) <= 60
    assert len(seo["meta_description"]) <= 160
    assert len(seo["alt_text"]) <= 220
