# FILE: apps/content-analysis/main.py
from __future__ import annotations

from contextlib import asynccontextmanager

import asyncpg
import httpx
import spacy
import structlog
from fastapi import FastAPI
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from redis.asyncio import Redis

from config import get_settings
from exceptions import ModuleProcessingError, module_exception_handler
from router import router


def configure_logging(level: str) -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )


def configure_tracing(service_name: str, service_version: str, otlp_endpoint: str) -> None:
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name, SERVICE_VERSION: service_version}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings.service_name, settings.service_version, settings.otlp_endpoint)

    app.state.settings = settings
    app.state.db_pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
    app.state.vector_db_pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
    app.state.redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    app.state.llm_client = httpx.AsyncClient(timeout=30.0)
    app.state.nlp_model = spacy.load("en_core_web_lg")

    yield

    await app.state.llm_client.aclose()
    await app.state.redis.aclose()
    await app.state.db_pool.close()
    await app.state.vector_db_pool.close()


app = FastAPI(title="content-analysis", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(ModuleProcessingError, module_exception_handler)
app.include_router(router)
