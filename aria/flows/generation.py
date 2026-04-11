# filename: flows/generation.py
# purpose: Step-by-step post generation orchestration using existing context, task, scoring, and repository layers.
# dependencies: asyncio, app.tasks, db.repositories.posts, services.context_assembly, services.variant_scorer

from __future__ import annotations

import asyncio
import json
from typing import Any

import asyncpg

from app.tasks import generate_audience, generate_caption, generate_hashtags, generate_seo_metadata
from db.connection import set_tenant
from db.repositories.posts import PostRepository
from services.context_assembly import ContextAssembler
from services.variant_scorer import VariantScorer


class GenerationOrchestrator:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.context = ContextAssembler(pool)
        self.scorer = VariantScorer(pool)
        self.posts = PostRepository(pool)

    async def _task_result(self, task, *args: Any, timeout: int = 120) -> dict[str, Any]:
        async_result = task.delay(*args)
        result = await asyncio.to_thread(async_result.get, timeout=timeout)
        if not isinstance(result, dict):
            raise ValueError("Task returned non-dict payload")
        return result

    async def run(self, company_id: str, post_id: str, request: dict[str, Any]) -> dict[str, Any]:
        # Step 1
        tone_profile, visual_profile, winner_examples, hashtag_priors = await asyncio.gather(
            self.context.fetch_tone_profile(company_id),
            self.context.fetch_visual_profile(company_id, request.get("media_asset_id")),
            self.context.fetch_winner_examples(company_id, request["platform_targets"], k=8),
            self.context.fetch_hashtag_priors(company_id, request["platform_targets"], k=50),
        )

        # Step 2
        hashtags_result, seo_result, audience_result = await asyncio.gather(
            self._task_result(
                generate_hashtags,
                company_id,
                {
                    "topic": request.get("core_message", ""),
                    "platform": request["platform_targets"][0],
                },
            ),
            self._task_result(
                generate_seo_metadata,
                company_id,
                {"caption_hash": post_id},
            ),
            self._task_result(
                generate_audience,
                company_id,
                {
                    "profile_hash": company_id,
                    "topic": request.get("core_message", ""),
                },
            ),
        )

        # Step 3
        caption_payload = {
            "company": company_id,
            "intent": request.get("intent", "announce"),
            "topic": request.get("core_message", ""),
            "platform": request["platform_targets"][0],
            "tone_profile": tone_profile,
            "visual_profile": visual_profile,
            "winner_examples": winner_examples,
            "hashtag_priors": hashtag_priors,
            "hashtags": hashtags_result,
            "seo": seo_result,
            "audience": audience_result,
        }
        caption_result = await self._task_result(generate_caption, company_id, caption_payload)

        variants: list[dict[str, Any]] = []
        hashtags = hashtags_result.get("hashtags", []) if isinstance(hashtags_result, dict) else []
        for platform in request["platform_targets"]:
            variants.append(
                {
                    "platform": platform,
                    "text": caption_result.get("caption", ""),
                    "tone": caption_result.get("tone", "neutral"),
                    "hashtags": hashtags,
                    "seo": seo_result,
                    "audience": audience_result,
                }
            )

        # Step 4
        ranked = await self.scorer.score_and_rank(
            company_id=company_id,
            variants=variants,
            platform=request["platform_targets"][0],
            tone_profile=tone_profile,
        )
        selected_variant = ranked[0] if ranked else {}
        quality_score = float(selected_variant.get("score", 0.0))

        # Step 5
        package = {
            "post_id": post_id,
            "context": {
                "tone_profile": tone_profile,
                "visual_profile": visual_profile,
                "winner_examples": winner_examples,
                "hashtag_priors": hashtag_priors,
            },
            "step_outputs": {
                "hashtags": hashtags_result,
                "seo": seo_result,
                "audience": audience_result,
                "caption": caption_result,
            },
            "variants": ranked,
            "selected_variant": selected_variant,
            "quality_score": quality_score,
        }
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await conn.execute("DELETE FROM post_variants WHERE post_id = $1::uuid", post_id)

                selected_variant_id: str | None = None
                persisted_ranked: list[dict[str, Any]] = []
                for idx, variant in enumerate(ranked[:3], start=1):
                    text = str(variant.get("text") or "")
                    scores_json = {
                        "score": float(variant.get("score", 0.0)),
                        "tone": variant.get("tone"),
                        "hashtags": variant.get("hashtags", []),
                    }
                    row = await conn.fetchrow(
                        """
                        INSERT INTO post_variants (
                            post_id, company_id, platform, variant_order,
                            text, char_count, scores_json, is_selected
                        ) VALUES (
                            $1::uuid, $2::uuid, $3, $4,
                            $5, $6, $7::jsonb, $8
                        )
                        RETURNING variant_id
                        """,
                        post_id,
                        company_id,
                        str(variant.get("platform", "")),
                        idx,
                        text,
                        len(text),
                        json.dumps(scores_json),
                        idx == 1,
                    )
                    stored = dict(variant)
                    stored["variant_id"] = str(row["variant_id"])
                    persisted_ranked.append(stored)
                    if idx == 1:
                        selected_variant_id = str(row["variant_id"])

                if selected_variant_id is not None:
                    await conn.execute(
                        "UPDATE posts SET selected_variant_id = $2::uuid, updated_at = now() WHERE post_id = $1::uuid",
                        post_id,
                        selected_variant_id,
                    )

                await self.posts.attach_generated_package(post_id, package, quality_score, conn=conn)
                await self.posts.update_status(post_id, "generated", conn=conn)

        if ranked:
            ranked = persisted_ranked
            selected_variant = ranked[0]

        return {
            "post_id": post_id,
            "variants": ranked,
            "selected_variant": selected_variant,
            "quality_score": quality_score,
        }
