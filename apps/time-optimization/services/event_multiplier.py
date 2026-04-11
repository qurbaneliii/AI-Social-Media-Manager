# FILE: apps/time-optimization/services/event_multiplier.py
from __future__ import annotations

from datetime import date


class EventMultiplier:
    def __init__(self) -> None:
        pass

    async def process(self, windows: list[dict], event_calendar: list[dict], run_date: date) -> list[dict]:
        """Apply multiplicative uplift when event impact exceeds 0.3 for matching date."""
        impacts = [e["impact"] for e in event_calendar if e["impact"] > 0.3 and e["date"] == run_date]
        factor = 1.0
        for impact in impacts:
            factor *= 1.0 + float(impact)
        for row in windows:
            row["score"] *= factor
        return windows
