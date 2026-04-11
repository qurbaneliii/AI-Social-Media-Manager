# FILE: apps/content-analysis/tests/test_services.py
from __future__ import annotations

import numpy as np
import pytest

from services.engagement_correlation import EngagementCorrelationUnit
from services.fingerprint_composer import FingerprintComposer
from services.ingestion_parser import IngestionParser


@pytest.mark.asyncio
async def test_ingestion_parser_step() -> None:
    parser = IngestionParser()

    class P:
        sample_posts = [type("S", (), {"text": " hello   world "})(), type("S", (), {"text": "second"})()]

    out = await parser.process(P())
    assert out == ["hello world", "second"]


@pytest.mark.asyncio
async def test_engagement_correlation_step() -> None:
    unit = EngagementCorrelationUnit()
    tfidf = np.array([[0.2, 0.3], [0.4, 0.5], [0.1, 0.2]])
    corr = await unit.process(tfidf, [0.1, 0.2, 0.3])
    assert isinstance(corr, float)


@pytest.mark.asyncio
async def test_sparse_sample_failure_mode_caps_confidence() -> None:
    composer = FingerprintComposer(0.4, 0.35, 0.25, 0.65)
    fp, conf, degraded = await composer.process({"tone": 0.8}, [0.1, 0.2], 0.3, sample_count=5)
    assert degraded is True
    assert conf == 0.65
    assert fp["confidence"] == 0.65
