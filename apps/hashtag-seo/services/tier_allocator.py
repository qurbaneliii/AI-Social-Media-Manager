# FILE: apps/hashtag-seo/services/tier_allocator.py
from __future__ import annotations

from config import Settings


class TierAllocator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _tier(self, volume: int) -> str:
        if volume >= self.settings.broad_threshold:
            return "broad"
        if self.settings.niche_lower <= volume <= self.settings.niche_upper:
            return "niche"
        if volume <= self.settings.micro_upper:
            return "micro"
        return "niche"

    async def process(self, scored: list[dict]) -> list[dict]:
        """Enforce exact tier quotas and borrow from adjacent tiers with penalty multiplier."""
        buckets = {"broad": [], "niche": [], "micro": []}
        for row in scored:
            tier = self._tier(int(row["search_volume"]))
            buckets[tier].append({**row, "tier": tier})

        selected: list[dict] = []
        quotas = {"broad": self.settings.broad_quota, "niche": self.settings.niche_quota, "micro": self.settings.micro_quota}
        order = ["broad", "niche", "micro"]

        for tier in order:
            selected.extend(buckets[tier][: quotas[tier]])

        for tier in order:
            deficit = quotas[tier] - len([s for s in selected if s["tier"] == tier])
            if deficit <= 0:
                continue
            adjacent = {"broad": "niche", "niche": "micro", "micro": "niche"}[tier]
            pool = [r for r in buckets[adjacent] if r not in selected]
            for row in pool[:deficit]:
                selected.append({**row, "tier": tier, "score": row["score"] * self.settings.borrow_penalty})

        selected.sort(key=lambda x: x["score"], reverse=True)
        return selected[: sum(quotas.values())]
