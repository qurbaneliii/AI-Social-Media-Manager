# FILE: apps/time-optimization/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from config import Settings
from models.input import TimeOptimizationInput
from models.output import RankedWindow, TimeOptimizationOutput
from services.baseline_loader import IndustryBaselineLoader
from services.competitor_penalty import CompetitorPenalty
from services.cooldown_enforcer import CooldownEnforcer
from services.event_multiplier import EventMultiplier
from services.uplift_estimator import UpliftEstimator

log = structlog.get_logger(__name__)


class TimeOptimizationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.baseline = IndustryBaselineLoader("apps/time-optimization/data/industry_baselines.json")
        self.uplift = UpliftEstimator()
        self.events = EventMultiplier()
        self.penalty = CompetitorPenalty()
        self.cooldown = CooldownEnforcer()

    async def run(self, payload: TimeOptimizationInput) -> TimeOptimizationOutput:
        """Execute ranking with cold-start blend, event multipliers, penalties, and cooldown."""
        log.info("request_received", company_id=str(payload.company_id))

        all_windows: list[RankedWindow] = []
        degraded_mode = False

        for platform in payload.target_platforms:
            baseline_windows = await self.baseline.process(payload.industry.lower(), platform.value)
            uplift_windows = await self.uplift.process(payload.historical_posts, platform.value)

            if len(payload.historical_posts) < 20:
                degraded_mode = True
                merged = []
                for row in baseline_windows:
                    merged_score = self.settings.cold_start_baseline_weight * float(row["score"]) + self.settings.cold_start_benchmark_weight * float(row["score"])
                    merged.append({"dow": row["dow"], "hour": row["hour"], "score": merged_score})
                confidence_cap = self.settings.cold_start_max_confidence
                log.warning("fallback_activated", fallback="cold_start", platform=platform.value)
            else:
                merged = uplift_windows or baseline_windows
                confidence_cap = 0.95

            merged = await self.events.process(merged, [e.model_dump() for e in payload.event_calendar], datetime.now(tz=timezone.utc).date())
            merged = await self.penalty.process(merged, float(payload.competitor_activity_density.get(platform.value, 0.0)))
            merged = await self.cooldown.process(merged, int(payload.posting_frequency_goal.get(platform.value, 1)))

            for row in merged[:5]:
                conf = max(0.0, min(confidence_cap, float(row["score"]) / max(float(merged[0]["score"]), 1e-6)))
                all_windows.append(
                    RankedWindow(
                        platform=platform,
                        dow=int(row["dow"]),
                        hour=int(row["hour"]),
                        score=float(row["score"]),
                        confidence=conf,
                    )
                )

        all_windows.sort(key=lambda w: w.score, reverse=True)
        confidence = sum(w.confidence for w in all_windows[:5]) / max(len(all_windows[:5]), 1)
        if confidence <= 0.65:
            log.warning("low_confidence_result", confidence_score=confidence)

        return TimeOptimizationOutput(
            company_id=payload.company_id,
            windows=all_windows,
            confidence_score=max(0.0, min(1.0, confidence)),
            degraded_mode=degraded_mode,
            generated_at=datetime.now(tz=timezone.utc),
        )
