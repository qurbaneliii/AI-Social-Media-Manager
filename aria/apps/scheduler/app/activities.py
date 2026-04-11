from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from temporalio import activity


@activity.defn(name="ValidateRequest")
async def validate_request(data: dict[str, Any]) -> dict[str, Any]:
    if not data.get("post_id"):
        raise ValueError("post_id is required")
    return data


@activity.defn(name="TriggerParallelModules")
async def trigger_parallel_modules(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": {"ok": True},
        "visual": {"ok": True},
        "hashtag": {"ok": True},
        "audience": {"ok": True},
        "time": {"ok": True},
    }


@activity.defn(name="WaitForModuleResults")
async def wait_for_module_results(results: dict[str, Any]) -> dict[str, Any]:
    return results


@activity.defn(name="ConsolidateAndScore")
async def consolidate_and_score(results: dict[str, Any]) -> dict[str, Any]:
    return {"score": 0.87, "results": results}


@activity.defn(name="DeliverPackage")
async def deliver_package(scored: dict[str, Any]) -> dict[str, Any]:
    return {"status": "generated", "package": scored}


@activity.defn(name="LoadCredentials")
async def load_credentials(data: dict[str, Any]) -> dict[str, Any]:
    return {"token": "decrypted-token", **data}


@activity.defn(name="ApprovalGate")
async def approval_gate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("approval_mode", "auto")
    approved = data.get("approved", mode == "auto")
    if mode == "human" and not approved:
        return {"paused": True, **data}
    return {"paused": False, **data}


@activity.defn(name="PublishToAdapter")
async def publish_to_adapter(data: dict[str, Any]) -> dict[str, Any]:
    fail_count = int(data.get("fail_count", 0))
    if fail_count > 0:
        data["fail_count"] = fail_count - 1
        raise RuntimeError("Simulated publish failure")
    return {"external_post_id": f"ext_{data['schedule_id']}", **data}


@activity.defn(name="ConfirmExternalID")
async def confirm_external_id(data: dict[str, Any]) -> dict[str, Any]:
    if not data.get("external_post_id"):
        raise ValueError("External post ID missing")
    return data


@activity.defn(name="ScheduleMetricsPull")
async def schedule_metrics_pull(data: dict[str, Any]) -> dict[str, Any]:
    return {"metrics_pull_at": (datetime.now(tz=timezone.utc) + timedelta(hours=6)).isoformat(), **data}


@activity.defn(name="EmitDeadLetter")
async def emit_dead_letter(data: dict[str, Any]) -> dict[str, Any]:
    return {"dead_letter_emitted": True, **data}


@activity.defn(name="NotifyUser")
async def notify_user(data: dict[str, Any]) -> dict[str, Any]:
    return {"notified": True, **data}


@activity.defn(name="IngestMetrics")
async def ingest_metrics(data: dict[str, Any]) -> dict[str, Any]:
    return {"ingested": True, **data}


@activity.defn(name="ScorePost")
async def score_post(data: dict[str, Any]) -> dict[str, Any]:
    return {"post_score": 0.79, **data}


@activity.defn(name="UpdateHashtagWeights")
async def update_hashtag_weights(data: dict[str, Any]) -> dict[str, Any]:
    return {"hashtag_weights_updated": True, **data}


@activity.defn(name="UpdatePostingWindowWeights")
async def update_posting_window_weights(data: dict[str, Any]) -> dict[str, Any]:
    return {"posting_window_weights_updated": True, **data}


@activity.defn(name="CheckDegradationThreshold")
async def check_degradation_threshold(data: dict[str, Any]) -> dict[str, Any]:
    degradation = random.random() * 0.2
    return {"degradation": degradation, "recalibration_required": degradation >= 0.12, **data}


@activity.defn(name="TriggerRecalibrationIfNeeded")
async def trigger_recalibration_if_needed(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("recalibration_required"):
        return {"recalibration_triggered": True, **data}
    return {"recalibration_triggered": False, **data}
