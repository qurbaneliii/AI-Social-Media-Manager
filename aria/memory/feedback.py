# filename: memory/feedback.py
# purpose: Performance metrics ingestion, normalized scoring, and winner labeling logic.
# dependencies: logging, datetime, asyncpg, pydantic

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg
from pydantic import BaseModel, ConfigDict, Field

from db.connection import set_tenant

logger = logging.getLogger(__name__)


class WebhookMetricPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    post_id: str | None = None
    platform: str
    external_post_id: str | None = None
    impressions: int = Field(ge=0)
    reach: int = Field(ge=0)
    engagement_rate: float = Field(ge=0.0)
    click_through_rate: float = Field(ge=0.0)
    saves: int = Field(ge=0)
    shares: int = Field(ge=0)
    follower_growth_delta: int = 0
    posting_timestamp: datetime
    captured_at: datetime


class PerformanceIngester:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def ingest_webhook(self, payload: dict[str, Any]) -> None:
        data = WebhookMetricPayload.model_validate(payload)
        query = """
        INSERT INTO performance_metrics (
            company_id, post_id, platform, external_post_id,
            impressions, reach, engagement_rate, click_through_rate,
            saves, shares, follower_growth_delta,
            posting_timestamp, captured_at, source
        ) VALUES (
            $1::uuid, $2::uuid, $3, $4,
            $5, $6, $7, $8,
            $9, $10, $11,
            $12, $13, 'webhook'
        )
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, data.company_id)
                await conn.execute(
                    query,
                    data.company_id,
                    data.post_id,
                    data.platform,
                    data.external_post_id,
                    data.impressions,
                    data.reach,
                    data.engagement_rate,
                    data.click_through_rate,
                    data.saves,
                    data.shares,
                    data.follower_growth_delta,
                    data.posting_timestamp,
                    data.captured_at,
                )

    async def ingest_pull(self, company_id: str, platform: str, records: list[dict[str, Any]]) -> None:
        if not records:
            return

        query = """
        INSERT INTO performance_metrics (
            company_id, post_id, platform, external_post_id,
            impressions, reach, engagement_rate, click_through_rate,
            saves, shares, follower_growth_delta,
            posting_timestamp, captured_at, source
        ) VALUES (
            $1::uuid, $2::uuid, $3, $4,
            $5, $6, $7, $8,
            $9, $10, $11,
            $12, $13, 'pull'
        )
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                for record in records:
                    posting_timestamp = record.get("posting_timestamp")
                    captured_at = record.get("captured_at", datetime.now(timezone.utc))
                    await conn.execute(
                        query,
                        company_id,
                        record.get("post_id"),
                        platform,
                        record.get("external_post_id"),
                        int(record.get("impressions", 0)),
                        int(record.get("reach", 0)),
                        float(record.get("engagement_rate", 0.0)),
                        float(record.get("click_through_rate", 0.0)),
                        int(record.get("saves", 0)),
                        int(record.get("shares", 0)),
                        int(record.get("follower_growth_delta", 0)),
                        posting_timestamp,
                        captured_at,
                    )

    async def compute_score(self, metric_row: dict[str, Any]) -> float:
        company_id = str(metric_row["company_id"])
        platform = str(metric_row["platform"])

        query = """
        SELECT
          percentile_cont(0.9) WITHIN GROUP (ORDER BY engagement_rate) AS p90_engagement,
          percentile_cont(0.9) WITHIN GROUP (ORDER BY click_through_rate) AS p90_ctr,
          percentile_cont(0.9) WITHIN GROUP (ORDER BY follower_growth_delta) AS p90_reach_growth,
          percentile_cont(0.9) WITHIN GROUP (ORDER BY (saves + shares)) AS p90_save_share
        FROM performance_metrics
        WHERE company_id = $1::uuid
          AND platform = $2
          AND captured_at >= now() - interval '90 days'
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                row = await conn.fetchrow(query, company_id, platform)

        p90_engagement = float(row["p90_engagement"] or 1.0)
        p90_ctr = float(row["p90_ctr"] or 1.0)
        p90_reach_growth = float(row["p90_reach_growth"] or 1.0)
        p90_save_share = float(row["p90_save_share"] or 1.0)

        engagement_norm = float(metric_row.get("engagement_rate", 0.0)) / max(p90_engagement, 1e-9)
        ctr_norm = float(metric_row.get("click_through_rate", 0.0)) / max(p90_ctr, 1e-9)
        reach_growth_norm = float(metric_row.get("follower_growth_delta", 0.0)) / max(p90_reach_growth, 1e-9)
        save_share_norm = (
            float(metric_row.get("saves", 0)) + float(metric_row.get("shares", 0))
        ) / max(p90_save_share, 1e-9)

        score = (
            0.35 * engagement_norm
            + 0.25 * ctr_norm
            + 0.20 * reach_growth_norm
            + 0.20 * save_share_norm
        )

        return max(0.0, min(1.0, float(score)))

    async def label_winners(self, company_id: str, platform: str) -> int:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                score_rows = await conn.fetch(
                    """
                    SELECT post_id,
                           avg(engagement_rate) AS engagement_rate,
                           avg(click_through_rate) AS click_through_rate,
                           avg(follower_growth_delta) AS follower_growth_delta,
                           avg(saves) AS saves,
                           avg(shares) AS shares
                    FROM performance_metrics
                    WHERE company_id = $1::uuid
                      AND platform = $2
                      AND captured_at >= now() - interval '90 days'
                      AND post_id IS NOT NULL
                    GROUP BY post_id
                    """,
                    company_id,
                    platform,
                )

                if not score_rows:
                    return 0

                for row in score_rows:
                    score = await self.compute_score(dict(row) | {"company_id": company_id, "platform": platform})
                    await conn.execute(
                        "UPDATE posts SET quality_score = $2, updated_at = now() WHERE post_id = $1::uuid",
                        str(row["post_id"]),
                        score,
                    )

                threshold_row = await conn.fetchrow(
                    """
                    SELECT percentile_cont(0.8) WITHIN GROUP (ORDER BY quality_score) AS p80
                    FROM posts
                    WHERE company_id = $1::uuid
                      AND created_at >= now() - interval '90 days'
                      AND quality_score IS NOT NULL
                    """,
                    company_id,
                )
                p80 = float(threshold_row["p80"] or 0.0)

                winner_rows = await conn.fetch(
                    """
                    UPDATE posts
                    SET generated_package_json = coalesce(generated_package_json, '{}'::jsonb) || '{"winner": true}'::jsonb,
                        updated_at = now()
                    WHERE company_id = $1::uuid
                      AND created_at >= now() - interval '90 days'
                      AND quality_score >= $2
                    RETURNING post_id
                    """,
                    company_id,
                    p80,
                )
                return len(winner_rows)
