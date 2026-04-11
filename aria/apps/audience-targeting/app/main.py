from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import redis
from fastapi import Depends, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sqlalchemy import create_engine


class AudienceInput(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    segments: list[str] = Field(default_factory=list)
    persona_summary: str
    platforms: list[str]


class AudienceOutput(BaseModel):
    audience: dict[str, Any]
    emitted_event: dict[str, Any]


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA Audience Targeting Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "audience-targeting"}


@app.post("/run", response_model=AudienceOutput)
def run_audience(payload: AudienceInput, deps: Dependencies = Depends(get_deps)) -> AudienceOutput:
    base_segments = payload.segments or ["awareness", "consideration"]
    psychographics = [
        "value-focused" if "B2B" in base_segments else "aspirational",
        "time-sensitive" if "promo" in payload.persona_summary.lower() else "research-oriented",
    ]

    per_platform = {}
    for platform in payload.platforms:
        per_platform[platform] = {
            "primary_segment": base_segments[0],
            "secondary_segment": base_segments[-1],
            "content_angle": f"{platform}-optimized narrative for {base_segments[0]}",
        }

    audience = {
        "segments": base_segments,
        "persona_summary": payload.persona_summary,
        "psychographics": psychographics,
        "platform_mapping": per_platform,
    }

    deps.cache.setex(f"audience:{payload.post_id}", 3600, str(audience))

    event = {
        "event_id": f"evt-{payload.post_id}-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "event_type": "module.result.ready.v1",
        "tenant_id": payload.tenant_id,
        "company_id": payload.company_id,
        "schema_version": 1,
        "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": {
            "module": "audience_targeting",
            "post_id": payload.post_id,
            "audience": audience,
        },
    }

    return AudienceOutput(audience=audience, emitted_event=event)
