# FILE: apps/content-analysis/services/engagement_correlation.py
from __future__ import annotations

import numpy as np
from scipy.stats import pearsonr


class EngagementCorrelationUnit:
    def __init__(self) -> None:
        pass

    async def process(self, tfidf_matrix: np.ndarray, engagement_rates: list[float | None]) -> float:
        """Compute Pearson correlation between aggregate TF-IDF activity and engagement rates."""
        valid_pairs = [(row, rate) for row, rate in zip(tfidf_matrix, engagement_rates) if rate is not None]
        if len(valid_pairs) < 2:
            return 0.0

        x = np.array([float(row.mean()) for row, _ in valid_pairs], dtype=np.float64)
        y = np.array([float(rate) for _, rate in valid_pairs], dtype=np.float64)

        if np.allclose(x, x[0]) or np.allclose(y, y[0]):
            return 0.0

        corr, _ = pearsonr(x, y)
        return float(corr) if np.isfinite(corr) else 0.0
