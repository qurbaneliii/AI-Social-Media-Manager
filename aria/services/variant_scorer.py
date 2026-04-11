# filename: services/variant_scorer.py
# purpose: Deterministic variant scoring and ranking for post generation selection.
# dependencies: re, math, asyncpg

from __future__ import annotations

import math
import re
from typing import Any

import asyncpg

from db.connection import set_tenant


class VariantScorer:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @staticmethod
    def _syllables(word: str) -> int:
        w = re.sub(r"[^a-z]", "", word.lower())
        if not w:
            return 1
        groups = re.findall(r"[aeiouy]+", w)
        count = len(groups)
        if w.endswith("e") and count > 1:
            count -= 1
        return max(1, count)

    @classmethod
    def _flesch_reading_ease(cls, text: str) -> float:
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        words = re.findall(r"\b\w+\b", text)
        if not words:
            return 0.0
        sentence_count = max(1, len(sentences))
        word_count = len(words)
        syllable_count = sum(cls._syllables(w) for w in words)
        return 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)

    @staticmethod
    def _normalize_readability(score: float) -> float:
        return max(0.0, min(1.0, score / 100.0))

    @staticmethod
    def _platform_limit(platform: str) -> int:
        limits = {
            "instagram": 2200,
            "linkedin": 3000,
            "x": 280,
            "tiktok": 2200,
        }
        return limits.get(platform.lower(), 2200)

    async def _top_hashtags(self, company_id: str, platform: str) -> set[str]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                rows = await conn.fetch(
                    """
                    SELECT tag
                    FROM hashtag_library
                    WHERE company_id = $1::uuid AND platform = $2
                    ORDER BY avg_engagement_lift DESC
                    LIMIT 50
                    """,
                    company_id,
                    platform,
                )
        return {str(r["tag"]).lower().lstrip("#") for r in rows}

    async def score_and_rank(
        self,
        company_id: str,
        variants: list[dict[str, Any]],
        platform: str,
        tone_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        top_tags = await self._top_hashtags(company_id, platform)
        descriptors = [str(x).lower() for x in tone_profile.get("tone_descriptors", [])]
        limit = self._platform_limit(platform)

        scored: list[dict[str, Any]] = []
        for variant in variants:
            text = str(variant.get("text") or variant.get("caption") or "")
            hashtags = variant.get("hashtags") or []
            if not isinstance(hashtags, list):
                hashtags = []

            readability = self._normalize_readability(self._flesch_reading_ease(text))

            if descriptors:
                hits = sum(1 for d in descriptors if d in text.lower())
                tone_match = hits / len(descriptors)
            else:
                tone_match = 0.0

            if hashtags:
                quality_hits = sum(
                    1
                    for tag in hashtags
                    if str(tag).lower().lstrip("#") in top_tags
                )
                hashtag_quality = quality_hits / len(hashtags)
            else:
                hashtag_quality = 0.0

            char_count = len(text)
            if char_count <= limit:
                length_compliance = 1.0
            else:
                max_len = int(limit * 1.10)
                if char_count >= max_len:
                    length_compliance = 0.0
                else:
                    length_compliance = (max_len - char_count) / max(1, (max_len - limit))

            score = (
                0.30 * readability
                + 0.25 * tone_match
                + 0.25 * hashtag_quality
                + 0.20 * length_compliance
            )

            row = dict(variant)
            row["score"] = max(0.0, min(1.0, float(score)))
            scored.append(row)

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored
