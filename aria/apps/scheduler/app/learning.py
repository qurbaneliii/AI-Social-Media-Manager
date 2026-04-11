from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp
from typing import Any


@dataclass
class MetricPoint:
    impressions: int
    reach: int
    engagement_rate: float
    click_through_rate: float
    saves: int
    shares: int


@dataclass
class LearningResult:
    hashtag_weights: dict[str, float]
    posting_window_weights: dict[int, float]
    prompt_recalibration_required: bool
    brand_voice_embedding: list[float]
    events: list[dict[str, Any]]


def ingest_metrics_pipeline(records: list[MetricPoint]) -> dict[str, float]:
    if not records:
        return {"engagement_mean": 0.0, "ctr_mean": 0.0}
    engagement_mean = sum(r.engagement_rate for r in records) / len(records)
    ctr_mean = sum(r.click_through_rate for r in records) / len(records)
    return {"engagement_mean": engagement_mean, "ctr_mean": ctr_mean}


def update_hashtag_weights_job(metrics_summary: dict[str, float], current_weights: dict[str, float]) -> dict[str, float]:
    uplift = metrics_summary["engagement_mean"] * 0.3 + metrics_summary["ctr_mean"] * 0.7
    updated = {}
    for tag, weight in current_weights.items():
        updated[tag] = round(0.8 * weight + 0.2 * uplift, 6)
    return updated


def update_posting_window_weights_job(hourly_performance: dict[int, float]) -> dict[int, float]:
    total = sum(max(v, 0.0) for v in hourly_performance.values()) or 1.0
    return {hour: round(max(score, 0.0) / total, 6) for hour, score in hourly_performance.items()}


def prompt_recalibration_trigger_logic(previous_score: float, current_score: float, degradation_threshold: float = 0.08) -> bool:
    if previous_score <= 0:
        return False
    degradation = (previous_score - current_score) / previous_score
    return degradation >= degradation_threshold


def brand_voice_embedding_update_pipeline(term_weights: dict[str, float], dim: int = 16) -> list[float]:
    vec = [0.0] * dim
    for idx, (term, weight) in enumerate(sorted(term_weights.items())):
        pos = idx % dim
        vec[pos] += (sum(ord(c) for c in term) % 97) * weight
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [round(v / norm, 8) for v in vec]


def run_learning_cycle(
    metrics: list[MetricPoint],
    current_hashtag_weights: dict[str, float],
    hourly_performance: dict[int, float],
    previous_prompt_score: float,
    current_prompt_score: float,
    term_weights: dict[str, float],
) -> LearningResult:
    summary = ingest_metrics_pipeline(metrics)
    hashtags = update_hashtag_weights_job(summary, current_hashtag_weights)
    windows = update_posting_window_weights_job(hourly_performance)
    recalibration = prompt_recalibration_trigger_logic(previous_prompt_score, current_prompt_score)
    embedding = brand_voice_embedding_update_pipeline(term_weights)

    now = datetime.now(tz=timezone.utc).isoformat()
    events = [
        {
            "event_id": f"evt-metrics-{int(datetime.now(tz=timezone.utc).timestamp())}",
            "event_type": "performance.metrics.ingested.v1",
            "schema_version": 1,
            "emitted_at": now,
            "payload": summary,
        }
    ]
    if recalibration:
        events.append(
            {
                "event_id": f"evt-recal-{int(datetime.now(tz=timezone.utc).timestamp())}",
                "event_type": "prompt.recalibration.required.v1",
                "schema_version": 1,
                "emitted_at": now,
                "payload": {
                    "reason": "rolling degradation threshold crossed",
                    "degradation_score": round((previous_prompt_score - current_prompt_score) / max(previous_prompt_score, 1e-9), 6),
                    "window_start": now,
                    "window_end": now,
                    "triggered_at": now,
                },
            }
        )

    return LearningResult(
        hashtag_weights=hashtags,
        posting_window_weights=windows,
        prompt_recalibration_required=recalibration,
        brand_voice_embedding=embedding,
        events=events,
    )
