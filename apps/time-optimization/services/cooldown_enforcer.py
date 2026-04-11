# FILE: apps/time-optimization/services/cooldown_enforcer.py
from __future__ import annotations


class CooldownEnforcer:
    def __init__(self) -> None:
        pass

    async def process(self, windows: list[dict], posting_frequency_goal: int) -> list[dict]:
        """Keep windows respecting minimum hour gap derived from 24 / posting_frequency_goal."""
        min_gap = max(1, int(round(24 / max(posting_frequency_goal, 1))))
        selected: list[dict] = []
        for row in sorted(windows, key=lambda x: x["score"], reverse=True):
            keep = True
            for s in selected:
                gap = abs(int(s["hour"]) - int(row["hour"]))
                if gap < min_gap:
                    keep = False
                    break
            if keep:
                selected.append(row)
            if len(selected) >= 5:
                break
        return selected
