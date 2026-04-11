# FILE: apps/scheduler/services/metrics_normalizer.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from types_shared import MetricRecord, Platform


class MetricsNormalizer:
    def __init__(self) -> None:
        pass

    async def process(self, company_id: UUID, post_id: UUID, platform: str, raw: dict) -> MetricRecord:
        """Map platform-native metrics payload to canonical MetricRecord model."""
        return MetricRecord(
            company_id=company_id,
            post_id=post_id,
            platform=Platform(platform),
            external_post_id=str(raw.get("id", "unknown")),
            impressions=int(raw.get("impressions", raw.get("views", 0))),
            reach=int(raw.get("reach", raw.get("unique_views", 0))),
            engagement_rate=float(raw.get("engagement_rate", 0.0)),
            click_through_rate=float(raw.get("click_through_rate", raw.get("ctr", 0.0))),
            saves=int(raw.get("saves", 0)),
            shares=int(raw.get("shares", 0)),
            follower_growth_delta=int(raw.get("follower_growth_delta", 0)),
            posting_timestamp=datetime.now(tz=timezone.utc),
            captured_at=datetime.now(tz=timezone.utc),
            source="webhook",
            attributes=raw,
        )
