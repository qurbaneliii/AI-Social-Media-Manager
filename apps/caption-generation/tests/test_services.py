# FILE: apps/caption-generation/tests/test_services.py
from __future__ import annotations

import pytest

from services.policy_checker import PolicyComplianceChecker


@pytest.mark.asyncio
async def test_policy_reject_banned_word() -> None:
    checker = PolicyComplianceChecker()
    ok, _ = await checker.process("x", {"caption_text": "bad text", "policy_compliance_score": 0.95}, ["bad"])
    assert ok is False


@pytest.mark.asyncio
async def test_policy_accept_valid() -> None:
    checker = PolicyComplianceChecker()
    ok, _ = await checker.process("x", {"caption_text": "good text", "policy_compliance_score": 0.95}, ["bad"])
    assert ok is True
