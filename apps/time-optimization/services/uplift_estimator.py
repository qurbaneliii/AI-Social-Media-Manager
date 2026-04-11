# FILE: apps/time-optimization/services/uplift_estimator.py
from __future__ import annotations

import lightgbm as lgb
import numpy as np

from models.input import HistoricalPost


class UpliftEstimator:
    def __init__(self) -> None:
        self.model = lgb.LGBMRanker(objective="lambdarank", n_estimators=60)

    async def process(self, posts: list[HistoricalPost], platform: str) -> list[dict]:
        """Train LightGBM ranker with required feature set and produce scored windows."""
        filtered = [p for p in posts if p.platform.value == platform]
        if len(filtered) < 3:
            return []

        content_map = {name: idx for idx, name in enumerate(sorted({p.content_type for p in filtered}))}
        x = np.array(
            [
                [p.day_of_week, p.hour_of_day, 1.0, float(content_map[p.content_type]), p.recency_decay]
                for p in filtered
            ],
            dtype=np.float32,
        )
        y = np.array([p.engagement_rate for p in filtered], dtype=np.float32)
        groups = np.array([len(filtered)], dtype=np.int32)
        self.model.fit(x, y, group=groups)
        scores = self.model.predict(x)

        out = []
        for post, score in zip(filtered, scores):
            out.append({"dow": post.day_of_week, "hour": post.hour_of_day, "score": float(score)})
        return out
