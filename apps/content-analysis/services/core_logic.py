# FILE: apps/content-analysis/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog
from asyncpg import Pool

from config import Settings
from models.input import ContentAnalysisInput
from models.output import ContentAnalysisOutput, ToneFingerprint
from services.embedding_generator import EmbeddingGenerator
from services.engagement_correlation import EngagementCorrelationUnit
from services.ingestion_parser import IngestionParser
from services.language_unit import LanguageDetectionUnit
from services.nlp_feature_extractor import NLPFeatureExtractor
from services.fingerprint_composer import FingerprintComposer

log = structlog.get_logger(__name__)


class ContentAnalysisService:
    def __init__(
        self,
        settings: Settings,
        nlp_model: object,
        db_pool: Pool,
        vector_db_pool: Pool,
        llm_client: object,
    ) -> None:
        self.settings = settings
        self.db_pool = db_pool
        self.ingestion_parser = IngestionParser()
        self.language_unit = LanguageDetectionUnit(llm_client, settings.llm_proxy_url, settings.language_confidence_threshold)
        self.feature_extractor = NLPFeatureExtractor(nlp_model)
        self.correlation_unit = EngagementCorrelationUnit()
        self.composer = FingerprintComposer(
            descriptive_prior_weight=settings.descriptive_prior_weight,
            corpus_stats_weight=settings.corpus_stats_weight,
            engagement_delta_weight=settings.engagement_delta_weight,
            sparse_sample_confidence_cap=settings.sparse_sample_confidence_cap,
        )
        self.embedding_generator = EmbeddingGenerator(vector_db_pool)

    async def run(self, payload: ContentAnalysisInput) -> ContentAnalysisOutput:
        """Execute ordered processing stages with sparse-sample and language fallbacks."""
        log.info("request_received", company_id=str(payload.company_id), sample_count=len(payload.sample_posts))

        texts = await self.ingestion_parser.process(payload)
        log.info("step_completed", step="ingestion_parser", sample_count=len(texts))

        lang_result = await self.language_unit.process(texts, payload.target_locale)
        log.info("step_completed", step="language_detection", translated=lang_result.translated)

        features = await self.feature_extractor.process(lang_result.texts)
        log.info("step_completed", step="nlp_feature_extractor", term_count=len(features.tfidf_terms))

        engagement_rates = [post.engagement_rate for post in payload.sample_posts]
        correlation = await self.correlation_unit.process(features.tfidf_matrix, engagement_rates)
        log.info("step_completed", step="engagement_correlation", pearson=correlation)

        fingerprint, confidence, degraded_mode = await self.composer.process(
            descriptive_prior=payload.descriptive_prior,
            sentiment_scores=features.sentiment_scores,
            correlation=correlation,
            sample_count=len(payload.sample_posts),
        )
        log.info("step_completed", step="fingerprint_composer", confidence_score=confidence, degraded_mode=degraded_mode)

        embedding_dim = await self.embedding_generator.process(
            company_id=payload.company_id,
            embedding=features.embedding_vector,
            metadata_json={"dominant_topics": features.dominant_topics, "translated": lang_result.translated},
        )
        log.info("step_completed", step="embedding_generator", embedding_dim=embedding_dim)

        result = ContentAnalysisOutput(
            company_id=payload.company_id,
            tone_fingerprint=ToneFingerprint(
                dimensions=fingerprint,
                top_terms=features.tfidf_terms[:20],
                dominant_topics=features.dominant_topics[:10],
            ),
            embedding_dim=embedding_dim,
            confidence_score=confidence,
            translated=lang_result.translated,
            degraded_mode=degraded_mode,
            generated_at=datetime.now(tz=timezone.utc),
        )

        if result.degraded_mode:
            log.warning("fallback_activated", fallback="sparse_sample", confidence_score=result.confidence_score)
        if result.confidence_score <= 0.65:
            log.warning("low_confidence_result", confidence_score=result.confidence_score)

        log.info("response_returned", company_id=str(payload.company_id), confidence_score=result.confidence_score)
        return result
