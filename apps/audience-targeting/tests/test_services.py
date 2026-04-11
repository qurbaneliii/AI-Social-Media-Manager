# FILE: apps/audience-targeting/tests/test_services.py
from __future__ import annotations

import pytest

from services.conflict_resolver import ConflictResolver


@pytest.mark.asyncio
async def test_conflict_override_age_range() -> None:
    resolver = ConflictResolver()
    resolved, warnings = await resolver.process(
        {"age_range": {"min_age": 25, "max_age": 40}},
        {"age_range": {"min_age": 10, "max_age": 60}, "confidence": 0.7},
    )
    assert resolved["age_range"]["min_age"] == 25
    assert "AUDIENCE_OVERRIDE" in warnings
