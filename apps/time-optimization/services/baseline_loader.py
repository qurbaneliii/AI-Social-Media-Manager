# FILE: apps/time-optimization/services/baseline_loader.py
from __future__ import annotations

import json
from pathlib import Path


class IndustryBaselineLoader:
    def __init__(self, baseline_path: str) -> None:
        self.baseline_path = baseline_path
        self._cache: dict | None = None

    async def process(self, industry: str, platform: str) -> list[dict]:
        """Load baseline matrix from JSON file and return platform-specific windows."""
        if self._cache is None:
            self._cache = json.loads(Path(self.baseline_path).read_text(encoding="utf-8"))
        return list(self._cache.get(industry, {}).get(platform, []))
