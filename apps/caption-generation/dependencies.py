# FILE: apps/caption-generation/dependencies.py
from __future__ import annotations

from collections.abc import AsyncIterator

import asyncpg
import httpx
from aiobotocore.session import get_session
from fastapi import Depends, Request
from redis.asyncio import Redis

from config import Settings, get_settings


async def get_db_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.db_pool


async def get_vector_db(request: Request) -> asyncpg.Pool:
    return request.app.state.vector_db_pool


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_llm_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.llm_client


async def get_s3_client(request: Request) -> AsyncIterator[object]:
    session = get_session()
    settings: Settings = request.app.state.settings
    async with session.create_client("s3", region_name=settings.aws_region) as client:
        yield client


def get_settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
