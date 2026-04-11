# FILE: apps/scheduler/services/temporal_activities.py
from __future__ import annotations

from temporalio import activity


@activity.defn
async def validate_request(data: dict) -> dict:
    """Validate required fields for workflow execution."""
    required = ["schedule_id", "post_id", "company_id", "platform"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing field: {field}")
    return data


@activity.defn
async def publish_attempt(data: dict) -> dict:
    """Simulate publish attempt with deterministic failure mode control."""
    if data.get("force_fail", False):
        raise RuntimeError("publish failed")
    return {**data, "external_post_id": f"ext_{data['schedule_id']}"}


@activity.defn
async def metrics_ingest(data: dict) -> dict:
    """Simulate metrics ingestion activity for feedback workflow."""
    return {**data, "ingested": True}
