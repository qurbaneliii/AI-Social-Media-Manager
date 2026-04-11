# FILE: apps/caption-generation/services/policy_checker.py
from __future__ import annotations


class PolicyComplianceChecker:
    def __init__(self) -> None:
        self.platform_limits = {
            "instagram": 2200,
            "linkedin": 3000,
            "facebook": 63206,
            "x": 280,
            "tiktok": 2200,
            "pinterest": 500,
        }

    async def process(self, platform: str, variant: dict, banned_terms: list[str]) -> tuple[bool, dict]:
        """Reject variants for banned terms, platform char overflow, and policy score below threshold."""
        text = str(variant.get("caption_text", ""))
        lowered = text.lower()
        if any(term.lower() in lowered for term in banned_terms):
            return False, variant
        if len(text) > self.platform_limits[platform]:
            return False, variant
        if float(variant.get("policy_compliance_score", 1.0)) < 0.90:
            return False, variant
        return True, variant
