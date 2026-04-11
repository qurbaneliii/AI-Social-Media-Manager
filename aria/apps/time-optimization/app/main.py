from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import redis
from fastapi import Depends, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sqlalchemy import create_engine


class TimeOptimizeInput(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    platform: str
    timezone_name: str = "UTC"
    historical_engagement_by_hour: list[float] = Field(default_factory=lambda: [0.05] * 24)


class TimeWindow(BaseModel):
    run_at_utc: datetime
    confidence: float
    reason: str


class TimeOptimizeOutput(BaseModel):
    ranked_windows: list[TimeWindow]
    emitted_event: dict[str, Any]


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA Time Optimization Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "time-optimization"}


@app.post("/rank", response_model=TimeOptimizeOutput)
def rank_windows(payload: TimeOptimizeInput, deps: Dependencies = Depends(get_deps)) -> TimeOptimizeOutput:
    scores = np.array(payload.historical_engagement_by_hour[:24], dtype=float)
    if scores.size < 24:
        padded = np.pad(scores, (0, 24 - scores.size), constant_values=float(scores.mean() if scores.size else 0.05))
        scores = padded

    ranked_hours = list(np.argsort(scores)[::-1][:5])
    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)

    windows: list[TimeWindow] = []
    for h in ranked_hours:
        candidate = now + timedelta(hours=int((h - now.hour) % 24))
        confidence = float(min(0.99, max(0.1, scores[h] * 2)))
        windows.append(TimeWindow(run_at_utc=candidate, confidence=round(confidence, 4), reason=f"Top historical hour {h}"))

    deps.cache.setex(f"time-rank:{payload.post_id}", 3600, str([w.model_dump() for w in windows]))

    event = {
        "event_id": f"evt-{payload.post_id}-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "event_type": "module.result.ready.v1",
        "tenant_id": payload.tenant_id,
        "company_id": payload.company_id,
        "schema_version": 1,
        "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": {
            "module": "time_optimization",
            "post_id": payload.post_id,
            "ranked_windows": [w.model_dump(mode="json") for w in windows],
        },
    }

    return TimeOptimizeOutput(ranked_windows=windows, emitted_event=event)
