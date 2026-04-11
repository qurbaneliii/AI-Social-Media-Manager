# FILE: apps/time-optimization/services/competitor_penalty.py
from __future__ import annotations


class CompetitorPenalty:
    def __init__(self) -> None:
        pass

    async def process(self, windows: list[dict], competitor_density: float) -> list[dict]:
        """Apply score penalty when competitor activity density is high."""
        if competitor_density >= 0.6:
            for row in windows:
                row["score"] *= 0.75
        return windows
