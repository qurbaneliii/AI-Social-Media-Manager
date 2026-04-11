# filename: api/posts.py
# purpose: Post generation API endpoints for dispatch and retrieval.
# dependencies: asyncpg, fastapi, pydantic, db.connection, db.repositories.posts, app.tasks

from __future__ import annotations

from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.tasks import run_generation
from db.connection import set_tenant
from db.repositories.posts import PostRepository

router = APIRouter()
SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class GeneratePostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    post_intent: str
    core_message: str = Field(min_length=20, max_length=500)
    target_platforms: list[str] = Field(min_length=1)
    campaign_tag: str | None = None
    attached_media_id: str | None = None
    manual_keywords: list[str] | None = None
    urgency_level: str
    requested_publish_at: str | None = None


def _coerce_score_0_to_100(value: Any) -> float:
    score = float(value or 0.0)
    if score <= 1.0:
        return score * 100.0
    return score


def _build_generated_package(post: dict[str, Any], variants: list[dict[str, Any]]) -> dict[str, Any]:
    existing = dict(post.get("generated_package_json") or {})
    generated = existing.get("generated_package_json") if isinstance(existing.get("generated_package_json"), dict) else existing

    step_outputs = generated.get("step_outputs", {}) if isinstance(generated, dict) else {}
    hashtag_list = step_outputs.get("hashtags", {}).get("hashtags", []) if isinstance(step_outputs, dict) else []
    seo = step_outputs.get("seo", {}) if isinstance(step_outputs, dict) else {}
    audience = step_outputs.get("audience", {}) if isinstance(step_outputs, dict) else {}

    package = {
        "variants": generated.get("variants", variants),
        "selected_variant_id": str(post.get("selected_variant_id") or ""),
        "hashtag_set": generated.get(
            "hashtag_set",
            {
                "broad": [{"tag": t, "score": 0.5} for t in hashtag_list],
                "niche": [],
                "micro": [],
            },
        ),
        "audience_definition": generated.get(
            "audience_definition",
            {
                "primary_demographic": {
                    "age_range": "unknown",
                    "gender_split": {"female": 0, "male": 0, "non_binary": 0},
                    "locations": [],
                },
                "psychographic_profile": {"interests": [], "values": [], "pain_points": []},
                "platform_segments": {
                    "facebook_custom_audience": {"include_rules": [], "exclude_rules": []},
                    "linkedin_audience_attributes": {"job_titles": [], "industries": [], "seniority": []},
                    "x_interest_clusters": [],
                    "tiktok_interest_categories": [],
                },
                "natural_language_summary": str(audience),
                "confidence": 0.5,
            },
        ),
        "posting_schedule_recommendation": generated.get("posting_schedule_recommendation", []),
        "seo_metadata": generated.get(
            "seo_metadata",
            {
                "meta_title": str(seo.get("title", "")),
                "meta_description": str(seo.get("description", "")),
                "alt_text": "",
                "keywords": seo.get("keywords", []),
            },
        ),
        "content_quality_score": generated.get(
            "content_quality_score",
            {
                "overall": _coerce_score_0_to_100(post.get("quality_score")),
                "subscores": {
                    "engagement_prediction": _coerce_score_0_to_100(post.get("quality_score")),
                    "tone_match": _coerce_score_0_to_100(post.get("quality_score")),
                    "platform_compliance": _coerce_score_0_to_100(post.get("quality_score")),
                    "keyword_coverage": _coerce_score_0_to_100(post.get("quality_score")),
                    "cta_strength": _coerce_score_0_to_100(post.get("quality_score")),
                },
            },
        ),
    }

    if not package["selected_variant_id"] and variants:
        package["selected_variant_id"] = str(variants[0].get("variant_id", ""))

    return package


@router.post("/generate")
async def generate_post(payload: GeneratePostRequest, request: Request) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    posts = PostRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await set_tenant(conn, payload.company_id)
            post = await posts.create(
                company_id=payload.company_id,
                intent=payload.post_intent,
                core_message=payload.core_message,
                platform_targets=payload.target_platforms,
                created_by=None,
                campaign_tag=payload.campaign_tag,
                conn=conn,
            )
            post_id = str(post["post_id"])
            await posts.update_status(post_id, "generating", conn=conn)

    generation_payload = {
        "intent": payload.post_intent,
        "core_message": payload.core_message,
        "platform_targets": payload.target_platforms,
        "media_asset_id": payload.attached_media_id,
        "campaign_tag": payload.campaign_tag,
        "manual_keywords": payload.manual_keywords,
        "urgency_level": payload.urgency_level,
        "requested_publish_at": payload.requested_publish_at,
    }
    async_result = run_generation.delay(payload.company_id, post_id, generation_payload)
    return {
        "post_id": post_id,
        "status": "generating",
        "estimated_ready_seconds": 15,
        "task_id": async_result.id,
    }


@router.get("/{post_id}")
async def get_post(post_id: str, request: Request, company_id: str | None = None) -> dict[str, Any]:
    pool: asyncpg.Pool = request.app.state.db_pool
    posts = PostRepository(pool)

    async with pool.acquire() as conn:
        async with conn.transaction():
            if company_id:
                await set_tenant(conn, company_id)
            else:
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
            post = await posts.get_by_id(post_id=post_id, conn=conn)
            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")
            variants = await conn.fetch(
                "SELECT variant_id, platform, text, char_count, scores_json FROM post_variants WHERE post_id = $1::uuid ORDER BY variant_order ASC",
                post_id,
            )

    mapped_variants = []
    for variant in variants:
        scores_json = dict(variant["scores_json"] or {})
        mapped_variants.append(
            {
                "variant_id": str(variant["variant_id"]),
                "platform": str(variant["platform"]),
                "text": str(variant["text"]),
                "char_count": int(variant["char_count"]),
                "scores": {
                    "engagement_predicted": float(scores_json.get("engagement_predicted", scores_json.get("score", 0.0))),
                    "tone_match": float(scores_json.get("tone_match", scores_json.get("score", 0.0))),
                    "cta_presence": float(scores_json.get("cta_presence", scores_json.get("score", 0.0))),
                    "keyword_inclusion": float(scores_json.get("keyword_inclusion", scores_json.get("score", 0.0))),
                    "platform_compliance": float(scores_json.get("platform_compliance", scores_json.get("score", 0.0))),
                    "total": float(scores_json.get("score", 0.0)),
                },
            }
        )

    return {
        "post_id": str(post["post_id"]),
        "status": str(post.get("status", "unknown")),
        "generated_package_json": _build_generated_package(post, mapped_variants),
    }
