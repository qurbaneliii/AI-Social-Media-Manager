# FILE: apps/scheduler/tests/test_services.py
from __future__ import annotations

import pytest

from services.temporal_workflows import JITTER_COEFFICIENT, RETRY_SCHEDULE_SECONDS


def test_retry_schedule_exact() -> None:
    assert RETRY_SCHEDULE_SECONDS == [60, 300, 900, 2700, 7200]
    assert JITTER_COEFFICIENT == 0.20


@pytest.mark.asyncio
async def test_metrics_normalizer_step() -> None:
    from services.metrics_normalizer import MetricsNormalizer
    from uuid import uuid4

    out = await MetricsNormalizer().process(uuid4(), uuid4(), "instagram", {"id": "1", "impressions": 2, "reach": 2})
    assert out.platform.value == "instagram"
