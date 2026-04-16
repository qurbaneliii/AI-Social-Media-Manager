# FILE: apps/audience-targeting/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from config import Settings
from models.input import AudienceTargetingInput
from models.output import AgeRange, AudienceProfile, AudienceTargetingOutput
from services.baseline_builder import BaselineBuilder
from services.conflict_resolver import ConflictResolver
from services.llm_inference import LlmInference
from services.performance_signal_miner import PerformanceSignalMiner
from services.platform_segment_mapper import PlatformSegmentMapper

log = structlog.get_logger(__name__)


class AudienceTargetingService:
    def __init__(self, settings: Settings, db_pool: object, redis_client: object, llm_client: object) -> None:
        self.settings = settings
        self.baseline_builder = BaselineBuilder(db_pool)
        self.signal_miner = PerformanceSignalMiner(db_pool)
        self.llm = LlmInference(llm_client, settings.llm_proxy_url)
        self.mapper = PlatformSegmentMapper(redis_client)
        self.resolver = ConflictResolver()
        self.redis_client = redis_client

    async def run(self, payload: AudienceTargetingInput) -> AudienceTargetingOutput:
        """Execute full audience inference with baseline fallback and conflict override logic."""
        log.info("request_received", company_id=str(payload.company_id))

        company_baseline = await self.baseline_builder.process(payload.company_id)
        if not company_baseline:
            raw = await self.redis_client.get(f"aria:baseline:audience:{payload.industry_vertical}")
            company_baseline = {"segments": ["default"], "age_range": {"min_age": 25, "max_age": 45}}
            if raw:
                import json

                company_baseline = json.loads(raw)
            log.warning("fallback_activated", fallback="industry_baseline")
        log.info("step_completed", step="baseline_builder")

        top_segments = await self.signal_miner.process(payload.company_id)
        if not top_segments:
            top_segments = list(company_baseline.get("segments", ["default"]))[:5]
            log.warning("fallback_activated", fallback="missing_metrics")
        log.info("step_completed", step="performance_signal_miner", segments=top_segments)

        llm_inferred = await self.llm.process(payload.campaign_context, top_segments)
        log.info("step_completed", step="llm_inference")

        resolved, warning_codes = await self.resolver.process(company_baseline, llm_inferred)
        log.info("step_completed", step="conflict_resolution", warning_codes=warning_codes)

        platform_mapping = await self.mapper.process([p.value for p in payload.target_platforms], top_segments)
        log.info("step_completed", step="platform_segment_mapper")

        confidence = float(resolved.get("confidence", 0.6))
        requires_approval = confidence < 0.55
        if requires_approval:
            log.warning("low_confidence_result", confidence_score=confidence)

        profile = AudienceProfile(
            age_range=AgeRange(**resolved.get("age_range", {"min_age": 25, "max_age": 45})),
            segments=top_segments,
            psychographics=resolved.get("psychographics", {"value_seeking": 0.5}),
            platform_segments=platform_mapping,
        )

        return AudienceTargetingOutput(
            company_id=payload.company_id,
            profile=profile,
            warning_codes=warning_codes,
            confidence_score=max(0.0, min(1.0, confidence)),
            requires_approval=requires_approval,
            generated_at=datetime.now(tz=timezone.utc),
        )
