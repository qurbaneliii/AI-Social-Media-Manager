from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

import numpy as np
import redis
from fastapi import Depends, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine


class AnalysisInput(BaseModel):
    tenant_id: str
    company_id: str
    documents: list[str] = Field(default_factory=list)
    engagement_scores: list[float] = Field(default_factory=list)


class ToneFingerprint(BaseModel):
    sentiment_mean: float
    top_terms: list[str]
    topic_labels: list[str]
    engagement_weighted_terms: dict[str, float]


class AnalysisOutput(BaseModel):
    tone_fingerprint_json: ToneFingerprint
    embedding_vectors: list[list[float]]
    emitted_event: dict[str, Any]


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA Content Analysis Service")
FastAPIInstrumentor.instrument_app(app)


def _sentiment_score(text: str) -> float:
    positive = {"great", "excellent", "amazing", "growth", "win", "success", "happy"}
    negative = {"bad", "poor", "problem", "loss", "delay", "risk", "angry"}
    words = [w.strip(".,!?;:").lower() for w in text.split()]
    p = sum(1 for w in words if w in positive)
    n = sum(1 for w in words if w in negative)
    denom = max(len(words), 1)
    return (p - n) / denom


def _extract_topics(docs: list[str], top_n: int = 5) -> list[str]:
    token_counter: Counter[str] = Counter()
    for doc in docs:
        token_counter.update(w.strip(".,!?;:").lower() for w in doc.split() if len(w) > 3)
    return [w for w, _ in token_counter.most_common(top_n)]


def _embed_docs(docs: list[str]) -> list[list[float]]:
    if not docs:
        return []
    vectorizer = TfidfVectorizer(max_features=128)
    mat = vectorizer.fit_transform(docs).toarray()
    return mat.astype(float).tolist()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "content-analysis"}


@app.post("/run", response_model=AnalysisOutput)
def run_analysis(payload: AnalysisInput, deps: Dependencies = Depends(get_deps)) -> AnalysisOutput:
    docs = payload.documents or ["No prior content available"]
    sentiments = [_sentiment_score(doc) for doc in docs]
    top_terms = _extract_topics(docs)

    vectors = _embed_docs(docs)
    weighted: dict[str, float] = {}
    if vectors:
        tfidf_terms = top_terms[: min(10, len(top_terms))]
        avg_eng = float(np.mean(payload.engagement_scores)) if payload.engagement_scores else 0.5
        for term in tfidf_terms:
            weighted[term] = round(avg_eng + (len(term) / 20), 5)

    tone = ToneFingerprint(
        sentiment_mean=round(float(np.mean(sentiments)), 6),
        top_terms=top_terms,
        topic_labels=[f"topic_{idx+1}:{term}" for idx, term in enumerate(top_terms)],
        engagement_weighted_terms=weighted,
    )

    deps.cache.setex(
        f"brand-voice:{payload.company_id}",
        3600,
        tone.model_dump_json(),
    )

    event = {
        "event_id": f"evt-{payload.company_id}-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "event_type": "brand.voice.ready.v1",
        "tenant_id": payload.tenant_id,
        "company_id": payload.company_id,
        "schema_version": 1,
        "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": {
            "profile_version": 1,
            "embedding_count": len(vectors),
            "ready_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    }

    return AnalysisOutput(tone_fingerprint_json=tone, embedding_vectors=vectors, emitted_event=event)
