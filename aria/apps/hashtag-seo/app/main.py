from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import redis
from fastapi import Depends, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sqlalchemy import create_engine


class HashtagSeoInput(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    platform: str
    keywords: list[str] = Field(default_factory=list)
    top_terms: list[str] = Field(default_factory=list)


class HashtagCandidate(BaseModel):
    tag: str
    score: float


class HashtagSeoOutput(BaseModel):
    hashtags: list[HashtagCandidate]
    seo: dict[str, Any]
    emitted_event: dict[str, Any]


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA Hashtag and SEO Service")
FastAPIInstrumentor.instrument_app(app)

PLATFORM_CAPS = {
    "instagram": 30,
    "linkedin": 5,
    "facebook": 10,
    "x": 5,
    "tiktok": 12,
    "pinterest": 20,
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hashtag-seo"}


@app.post("/run", response_model=HashtagSeoOutput)
def run_hashtag_seo(payload: HashtagSeoInput, deps: Dependencies = Depends(get_deps)) -> HashtagSeoOutput:
    words = payload.keywords + payload.top_terms
    dedup = list(dict.fromkeys([w.lower().replace(" ", "") for w in words if w.strip()]))

    candidates: list[HashtagCandidate] = []
    for idx, word in enumerate(dedup):
        base = 1.0 / (idx + 1)
        score = round(base + (len(word) / 100), 5)
        candidates.append(HashtagCandidate(tag=f"#{word}", score=score))

    candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
    cap = PLATFORM_CAPS.get(payload.platform, 10)
    selected = candidates[:cap]

    seo = {
        "title": " ".join(payload.keywords[:6])[:60],
        "description": " ".join(payload.top_terms[:20])[:155],
        "slug": "-".join(payload.keywords[:8]).lower(),
        "focus_terms": payload.keywords[:8],
    }

    deps.cache.setex(f"hashtags:{payload.post_id}", 3600, str([h.model_dump() for h in selected]))

    event = {
        "event_id": f"evt-{payload.post_id}-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "event_type": "module.result.ready.v1",
        "tenant_id": payload.tenant_id,
        "company_id": payload.company_id,
        "schema_version": 1,
        "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": {
            "module": "hashtag_seo",
            "post_id": payload.post_id,
            "hashtags": [h.model_dump() for h in selected],
            "seo": seo,
        },
    }

    return HashtagSeoOutput(hashtags=selected, seo=seo, emitted_event=event)
