# filename: services/brand_analysis.py
# purpose: Brand analysis service combining tone calibration task output with NLP extraction and visual aggregation.
# dependencies: os, asyncio, collections, asyncpg, spacy, app.tasks, app.vision, db.repositories.brand_profiles

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import Counter
from typing import Any

import asyncpg
import spacy

from app.tasks import calibrate_tone
from app.vision import analyze_image
from db.connection import set_tenant
from db.repositories.brand_profiles import BrandProfileRepository


logger = logging.getLogger(__name__)


class BrandAnalyzer:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.brand_repo = BrandProfileRepository(pool)
        try:
            self._nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model en_core_web_sm is unavailable; falling back to blank English model")
            self._nlp = spacy.blank("en")

    async def run_tone_fingerprint(self, company_id: str) -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                rows = await conn.fetch(
                    """
                    SELECT text
                    FROM import_staging
                    WHERE company_id = $1::uuid
                    ORDER BY created_at DESC
                    """,
                    company_id,
                )
        corpus = "\n".join(str(row["text"]) for row in rows)
        if not corpus:
            raise ValueError("No staged import posts found for company")

        task = calibrate_tone.delay(
            company_id,
            {
                "brand_profile": f"company:{company_id}",
                "content": corpus[:12000],
            },
        )
        llm_result = await asyncio.to_thread(task.get, timeout=120)

        doc = self._nlp(corpus)
        keywords: list[str] = []
        for ent in doc.ents:
            val = ent.text.strip()
            if val:
                keywords.append(val)

        if "parser" in self._nlp.pipe_names:
            for chunk in doc.noun_chunks:
                val = chunk.text.strip()
                if val:
                    keywords.append(val)

        keyword_counts = Counter(k.lower() for k in keywords)
        top_keywords = [k for k, _ in keyword_counts.most_common(30)]

        result = {
            "tone_score": float(llm_result.get("tone_score", 0.0)),
            "suggested_tone": str(llm_result.get("suggested_tone", "neutral")),
            "keywords": top_keywords,
        }

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await self.brand_repo.update_analysis(
                    company_id=company_id,
                    tone_fingerprint_json=result,
                    confidence=float(result["tone_score"]),
                    conn=conn,
                )
        return result

    async def run_visual_extraction(self, company_id: str) -> dict[str, Any]:
        root = os.getenv("MEDIA_STORAGE_ROOT", "/tmp/aria-media")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                rows = await conn.fetch(
                    """
                    SELECT asset_id, s3_key
                    FROM media_assets
                    WHERE company_id = $1::uuid
                        AND status = 'uploaded'
                        AND visual_analysis IS NULL
                    """,
                    company_id,
                )

        analyses: list[dict[str, Any]] = []
        for row in rows:
            local_path = os.path.join(root, str(row["s3_key"]))
            if not os.path.exists(local_path):
                continue
            result = analyze_image(local_path)
            analyses.append(result)
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await set_tenant(conn, company_id)
                    await conn.execute(
                        "UPDATE media_assets SET visual_analysis = $2::jsonb WHERE asset_id = $1::uuid",
                        str(row["asset_id"]),
                        json.dumps(result),
                    )

        palette_counts: Counter[str] = Counter()
        layout_counts: Counter[str] = Counter()
        for item in analyses:
            for color in item.get("palette", []):
                palette_counts[str(color)] += 1
            layout_counts[str(item.get("layout_tag", "unknown"))] += 1

        visual_style_json = {
            "top_palette": [color for color, _ in palette_counts.most_common(10)],
            "layout_distribution": dict(layout_counts),
            "asset_count": len(analyses),
        }

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await self.brand_repo.update_analysis(
                    company_id=company_id,
                    visual_style_json=visual_style_json,
                    conn=conn,
                )
        return visual_style_json
