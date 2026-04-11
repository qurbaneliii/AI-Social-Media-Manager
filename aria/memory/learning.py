# filename: memory/learning.py
# purpose: Prompt learning logic for winner feature extraction, controlled prompt promotion, and decline detection.
# dependencies: logging, asyncpg

from __future__ import annotations

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_CTA_TOKENS = ["learn more", "buy now", "book demo", "download", "comment", "share"]


def _first_n_words(text: str, n: int) -> str:
    return " ".join(text.strip().split()[:n])


def _token_position_ratio(text: str, token: str) -> float:
    lower = text.lower()
    idx = lower.find(token.lower())
    if idx < 0 or len(lower) == 0:
        return 1.0
    return float(idx / len(lower))


class PromptLearner:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def extract_winner_features(self, company_id: str, platform: str) -> list[dict[str, Any]]:
        query = """
        SELECT p.post_id,
               pv.text AS caption,
               p.generated_package_json
        FROM posts p
        JOIN post_variants pv ON pv.post_id = p.post_id AND pv.is_selected = TRUE AND pv.platform = $2
        WHERE p.company_id = $1::uuid
          AND coalesce((p.generated_package_json->>'winner')::boolean, false) = true
        ORDER BY p.created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, company_id, platform)

        features: list[dict[str, Any]] = []
        for row in rows:
            caption = str(row["caption"] or "")
            package = row["generated_package_json"] or {}

            hook_style = _first_n_words(caption, 10)

            cta_ratio = 1.0
            for cta in _CTA_TOKENS:
                cta_ratio = min(cta_ratio, _token_position_ratio(caption, cta))

            primary_keyword = ""
            if isinstance(package, dict):
                keywords = package.get("keywords") or package.get("seo_keywords") or []
                if isinstance(keywords, list) and keywords:
                    primary_keyword = str(keywords[0])
            keyword_ratio = _token_position_ratio(caption, primary_keyword) if primary_keyword else 1.0

            tier_comp = {"broad": 0, "niche": 0, "micro": 0}
            if isinstance(package, dict):
                hashtag_tiers = package.get("hashtag_tier_composition")
                if isinstance(hashtag_tiers, dict):
                    for key in tier_comp:
                        tier_comp[key] = int(hashtag_tiers.get(key, 0))

            features.append(
                {
                    "post_id": str(row["post_id"]),
                    "hook_style": hook_style,
                    "cta_position": cta_ratio,
                    "keyword_position": keyword_ratio,
                    "hashtag_tier_composition": tier_comp,
                }
            )

        return features

    async def promote_template(
        self,
        module_name: str,
        candidate_version: int,
        control_version: int,
    ) -> bool:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT version, performance_score
                FROM prompt_templates
                WHERE module_name = $1
                  AND version = ANY($2::int[])
                """,
                module_name,
                [candidate_version, control_version],
            )
            score_map = {int(r["version"]): float(r["performance_score"] or 0.0) for r in rows}

            candidate = score_map.get(candidate_version)
            control = score_map.get(control_version)
            if candidate is None or control is None:
                return False

            sample_row = await conn.fetchrow(
                """
                SELECT count(*)::int AS n
                FROM posts
                WHERE context_snapshot_json->>'module_name' = $1
                  AND (context_snapshot_json->>'prompt_version')::int = ANY($2::int[])
                """,
                module_name,
                [candidate_version, control_version],
            )
            sample_size = int(sample_row["n"] or 0)
            if sample_size < 100:
                return False

            base = control if control > 0 else 1e-9
            uplift = (candidate - control) / base
            if uplift < 0.05:
                return False

            async with conn.transaction():
                await conn.execute(
                    "UPDATE prompt_templates SET active = FALSE WHERE module_name = $1",
                    module_name,
                )
                await conn.execute(
                    "UPDATE prompt_templates SET active = TRUE WHERE module_name = $1 AND version = $2",
                    module_name,
                    candidate_version,
                )
            return True

    async def detect_decline(self, company_id: str, platform: str) -> bool:
        query = """
        WITH current_window AS (
          SELECT avg(quality_score) AS avg_score
          FROM posts p
          JOIN post_variants pv ON pv.post_id = p.post_id AND pv.is_selected = TRUE
          WHERE p.company_id = $1::uuid
            AND pv.platform = $2
            AND p.created_at >= now() - interval '28 days'
            AND p.quality_score IS NOT NULL
        ),
        previous_window AS (
          SELECT avg(quality_score) AS avg_score
          FROM posts p
          JOIN post_variants pv ON pv.post_id = p.post_id AND pv.is_selected = TRUE
          WHERE p.company_id = $1::uuid
            AND pv.platform = $2
            AND p.created_at >= now() - interval '56 days'
            AND p.created_at < now() - interval '28 days'
            AND p.quality_score IS NOT NULL
        )
        SELECT
          coalesce((SELECT avg_score FROM current_window), 0.0) AS current_avg,
          coalesce((SELECT avg_score FROM previous_window), 0.0) AS previous_avg
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, company_id, platform)

        current_avg = float(row["current_avg"] or 0.0)
        previous_avg = float(row["previous_avg"] or 0.0)
        if previous_avg <= 0.0:
            return False

        drop = (previous_avg - current_avg) / previous_avg
        if drop > 0.15:
            logger.warning(
                "prompt.recalibration.required company_id=%s platform=%s drop=%.4f",
                company_id,
                platform,
                drop,
            )
            return True

        return False
