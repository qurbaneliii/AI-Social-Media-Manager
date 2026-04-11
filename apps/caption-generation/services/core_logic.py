# FILE: apps/caption-generation/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from config import Settings
from models.input import CaptionGenerationInput
from models.output import CaptionGenerationOutput, CaptionVariant
from services.context_assembler import ContextAssembler
from services.policy_checker import PolicyComplianceChecker
from services.provider_router import ProviderRouter
from services.scoring_engine import CaptionScoringEngine

log = structlog.get_logger(__name__)


class CaptionGenerationService:
    def __init__(self, settings: Settings, llm_client: object) -> None:
        self.settings = settings
        self.context = ContextAssembler()
        self.providers = ProviderRouter(llm_client, settings.llm_proxy_url)
        self.policy = PolicyComplianceChecker()
        self.score = CaptionScoringEngine(settings)

    async def run(self, payload: CaptionGenerationInput) -> CaptionGenerationOutput:
        """Generate per-platform variants with provider fallback and deterministic selection rules."""
        log.info("request_received", company_id=str(payload.company_id))
        accepted: list[CaptionVariant] = []

        for platform in payload.target_platforms:
            ctx = await self.context.process(payload, platform.value)
            raw_variants = await self.providers.process(ctx)

            for raw in raw_variants:
                raw.setdefault("caption_text", f"{payload.core_message} [{platform.value}]")
                raw.setdefault("policy_compliance_score", 0.95)
                raw.setdefault("cta_present", True)
                raw.setdefault("keyword_inclusion", 0.8)
                raw.setdefault("engagement_predicted", 0.7)
                raw.setdefault("tone_match", 0.7)
                raw.setdefault("platform_compliance", 1.0)
                ok, candidate = await self.policy.process(platform.value, raw, payload.banned_vocabulary_list)
                if not ok:
                    continue
                scored = await self.score.process(candidate)
                accepted.append(
                    CaptionVariant(
                        platform=platform,
                        caption_text=str(scored["caption_text"]),
                        policy_compliance_score=float(scored["policy_compliance_score"]),
                        engagement_predicted=float(scored["engagement_predicted"]),
                        tone_match=float(scored["tone_match"]),
                        cta_present=bool(scored["cta_present"]),
                        keyword_inclusion=float(scored["keyword_inclusion"]),
                        platform_compliance=float(scored["platform_compliance"]),
                        final_score=float(scored["final_score"]),
                    )
                )

        accepted.sort(key=lambda v: (v.platform.value, -v.final_score, -v.tone_match, -v.engagement_predicted))
        selected: dict[str, CaptionVariant] = {}
        for variant in accepted:
            if variant.platform.value not in selected:
                selected[variant.platform.value] = variant

        confidence = sum(v.final_score for v in selected.values()) / max(len(selected), 1)
        degraded = len(selected) < len(payload.target_platforms)
        if degraded:
            log.warning("fallback_activated", fallback="variant_filter_reduction")
        if confidence <= 0.65:
            log.warning("low_confidence_result", confidence_score=confidence)

        return CaptionGenerationOutput(
            company_id=payload.company_id,
            variants=accepted,
            selected_variants_by_platform=selected,
            confidence_score=max(0.0, min(1.0, confidence)),
            degraded_mode=degraded,
            generated_at=datetime.now(tz=timezone.utc),
        )
