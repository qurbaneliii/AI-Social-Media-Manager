# FILE: apps/time-optimization/tests/test_services.py
from __future__ import annotations

import pytest

from services.cooldown_enforcer import CooldownEnforcer
from services.competitor_penalty import CompetitorPenalty


@pytest.mark.asyncio
async def test_competitor_penalty_step() -> None:
    windows = [{"hour": 10, "score": 1.0}]
    out = await CompetitorPenalty().process(windows, 0.6)
    assert round(out[0]["score"], 2) == 0.75


@pytest.mark.asyncio
async def test_cooldown_enforcement_step() -> None:
    windows = [{"hour": 10, "score": 1.0}, {"hour": 11, "score": 0.9}, {"hour": 20, "score": 0.8}]
    out = await CooldownEnforcer().process(windows, posting_frequency_goal=2)
    assert len(out) >= 1
