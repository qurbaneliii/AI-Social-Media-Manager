# FILE: apps/hashtag-seo/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import structlog

from config import Settings
from models.input import HashtagSeoInput
from models.output import HashtagSeoOutput, RankedHashtag, SeoMetadata
from services.llm_candidate_generator import LlmCandidateGenerator
from services.merge_deduplicate import MergeDeduplicator
from services.policy_filter import PolicyFilter
from services.scoring_engine import ScoringEngine
from services.seo_metadata_generator import SeoMetadataGenerator
from services.tier_allocator import TierAllocator
from services.vector_retriever import VectorRetriever

log = structlog.get_logger(__name__)


class HashtagSeoService:
    def __init__(self, settings: Settings, llm_client: object, vector_db: object, redis_client: object) -> None:
        self.settings = settings
        self.llm_gen = LlmCandidateGenerator(llm_client, settings.llm_proxy_url)
        self.vector = VectorRetriever(vector_db)
        self.merge = MergeDeduplicator()
        self.policy = PolicyFilter(redis_client)
        self.scoring = ScoringEngine(settings)
        self.tiering = TierAllocator(settings)
        self.seo = SeoMetadataGenerator(settings)

    async def run(self, payload: HashtagSeoInput) -> HashtagSeoOutput:
        """Execute full hashtag pipeline with deterministic ranking and quotas."""
        log.info("request_received", company_id=str(payload.company_id), platform=payload.target_platform.value)
        llm_candidates = await self.llm_gen.process(payload.core_text, payload.keywords)
        log.info("step_completed", step="llm_candidate_generation", count=len(llm_candidates))

        probe_vector = np.ones(768, dtype=np.float32).tolist()
        vector_candidates = await self.vector.process(payload.company_id, payload.target_platform.value, probe_vector)
        log.info("step_completed", step="vector_retrieval", count=len(vector_candidates))

        merged = await self.merge.process(llm_candidates, vector_candidates)
        safe = await self.policy.process(payload.target_platform.value, payload.banned_tags, merged)
        log.info("step_completed", step="merge_dedup_policy", count=len(safe))

        scored = await self.scoring.process(safe, vector_candidates)
        selected = await self.tiering.process(scored)
        log.info("step_completed", step="scoring_tiering", selected=len(selected))

        metadata = await self.seo.process(payload.core_text, payload.keywords)
        result = HashtagSeoOutput(
            company_id=payload.company_id,
            hashtags=[RankedHashtag(hashtag=f"#{row['token']}", score=float(row["score"]), tier=row["tier"]) for row in selected],
            seo_metadata=SeoMetadata(**metadata),
            confidence_score=min(1.0, max(0.0, sum(r["score"] for r in selected[:5]) / max(len(selected[:5]), 1))),
            degraded_mode=False,
            generated_at=datetime.now(tz=timezone.utc),
        )

        if result.confidence_score <= 0.65:
            log.warning("low_confidence_result", confidence_score=result.confidence_score)
        log.info("response_returned", confidence_score=result.confidence_score)
        return result
