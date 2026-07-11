from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ai.agents import AIOrchestrator
from ai.schemas.brand import BrandProfile
from ai.schemas.content import ContentRequest, GeneratedContentPackage, PlatformContext
from api.dependencies import get_ai_orchestrator


router = APIRouter(tags=["public-runtime"])

PUBLIC_POST_STORE: dict[str, dict[str, Any]] = {}
PUBLIC_SCHEDULE_STORE: dict[str, dict[str, Any]] = {}


class PublicGeneratePostRequest(BaseModel):
    company_id: str
    post_intent: str
    core_message: str = Field(min_length=3, max_length=5000)
    target_platforms: list[str] = Field(min_length=1)
    campaign_tag: str | None = None
    attached_media_id: str | None = None
    manual_keywords: list[str] | None = None
    urgency_level: str = "immediate"
    requested_publish_at: str | None = None


class PublicSaveDraftRequest(BaseModel):
    company_id: str
    platform: str
    content: str = Field(min_length=3, max_length=5000)
    intent: str = "engage"
    campaign_tag: str | None = None
    topic: str | None = None
    tone: str | None = None
    cta: str | None = None


class PublicScheduleTarget(BaseModel):
    platform: str
    run_at_utc: str


class PublicScheduleRequest(BaseModel):
    post_id: str
    company_id: str
    targets: list[PublicScheduleTarget] = Field(min_length=1)
    approval_mode: str = "human"
    manual_override: dict[str, Any] | None = None


class PublicScheduleApprovalRequest(BaseModel):
    company_id: str | None = None
    approved_by: str | None = None


def _normalize_public_platform(platform: str) -> str:
    value = platform.strip().lower()
    if value == "twitter":
        return "x"
    allowed = {"linkedin", "instagram", "facebook", "x", "tiktok", "pinterest"}
    if value not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    return value


def _public_brand_profile(company_id: str, platforms: list[str], *, topic: str = "") -> BrandProfile:
    return BrandProfile(
        brand_id=company_id,
        brand_name="Selected brand",
        industry="social media",
        description="Brand context supplied by the public MVP route until Brand Brain is fully connected.",
        products_or_services=["social media content"],
        target_audience=["selected audience"],
        tone_of_voice=["clear", "professional"],
        brand_values=["truthful approval-based publishing"],
        forbidden_topics=[],
        forbidden_words=[],
        approved_claims=[],
        competitors=[],
        platforms=platforms,
        visual_style={},
        business_goals=[topic or "create approval-ready social content"],
        language_preferences=["en"],
    )


def _generated_package_for_frontend(post_id: str, package: GeneratedContentPackage) -> dict[str, Any]:
    text = "\n\n".join(part for part in (package.hook, package.caption, package.cta) if part).strip()
    score = package.quality_scores.engagement_potential_score * 100 if package.quality_scores else 0.0
    variant_id = f"{post_id}-{package.platform}"
    return {
        "variants": [
            {
                "variant_id": variant_id,
                "platform": package.platform,
                "text": text,
                "char_count": len(text),
                "provider_used": "llm-orchestration",
                "cached": False,
                "scores": {
                    "engagement_predicted": score,
                    "tone_match": package.quality_scores.brand_consistency_score * 100 if package.quality_scores else 0.0,
                    "cta_presence": package.quality_scores.cta_strength_score * 100 if package.quality_scores else 0.0,
                    "keyword_inclusion": 0.0,
                    "platform_compliance": package.quality_scores.platform_fit_score * 100 if package.quality_scores else 0.0,
                    "total": score,
                },
            }
        ],
        "selected_variant_id": variant_id,
        "hashtag_set": {
            "broad": [{"tag": tag, "score": 0.5} for tag in package.hashtags],
            "niche": [],
            "micro": [],
        },
        "audience_definition": {
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
            "natural_language_summary": package.rationale,
            "confidence": 0.5,
        },
        "posting_schedule_recommendation": [package.posting_recommendation] if package.posting_recommendation else [],
        "seo_metadata": {
            "meta_title": package.hook[:60],
            "meta_description": package.caption[:155],
            "alt_text": "",
            "keywords": [tag.lstrip("#") for tag in package.hashtags],
        },
        "content_quality_score": {
            "overall": score,
            "subscores": {
                "engagement_prediction": score,
                "tone_match": package.quality_scores.brand_consistency_score * 100 if package.quality_scores else 0.0,
                "platform_compliance": package.quality_scores.platform_fit_score * 100 if package.quality_scores else 0.0,
                "keyword_coverage": 0.0,
                "cta_strength": package.quality_scores.cta_strength_score * 100 if package.quality_scores else 0.0,
            },
        },
    }


def _draft_package_for_frontend(post_id: str, platform: str, content: str) -> dict[str, Any]:
    variant_id = f"{post_id}-{platform}"
    return {
        "variants": [
            {
                "variant_id": variant_id,
                "platform": platform,
                "text": content,
                "char_count": len(content),
                "provider_used": "user-draft",
                "cached": False,
                "scores": {
                    "engagement_predicted": 0.0,
                    "tone_match": 0.0,
                    "cta_presence": 0.0,
                    "keyword_inclusion": 0.0,
                    "platform_compliance": 0.0,
                    "total": 0.0,
                },
            }
        ],
        "selected_variant_id": variant_id,
        "hashtag_set": {"broad": [], "niche": [], "micro": []},
        "audience_definition": {
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
            "natural_language_summary": "",
            "confidence": 0.0,
        },
        "posting_schedule_recommendation": [],
        "seo_metadata": {"meta_title": "", "meta_description": "", "alt_text": "", "keywords": []},
        "content_quality_score": {
            "overall": 0.0,
            "subscores": {
                "engagement_prediction": 0.0,
                "tone_match": 0.0,
                "platform_compliance": 0.0,
                "keyword_coverage": 0.0,
                "cta_strength": 0.0,
            },
        },
    }


@router.post("/v1/posts/generate")
async def public_generate_post(
    payload: PublicGeneratePostRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> dict[str, Any]:
    platform = _normalize_public_platform(payload.target_platforms[0])
    post_id = str(uuid4())
    brand_profile = _public_brand_profile(
        payload.company_id,
        [_normalize_public_platform(item) for item in payload.target_platforms],
        topic=payload.core_message,
    )
    package = await orchestrator.generate_content_package(
        ContentRequest(
            brand_profile=brand_profile,
            platform_context=PlatformContext(
                platform=platform,
                content_type="post",
                objective=payload.post_intent,
            ),
            campaign_objective=payload.campaign_tag or payload.post_intent,
            topic=payload.core_message,
            content_pillar=payload.post_intent,
            extra_context={
                "manual_keywords": payload.manual_keywords or [],
                "urgency_level": payload.urgency_level,
                "requested_publish_at": payload.requested_publish_at,
                "attached_media_id": payload.attached_media_id,
            },
        )
    )
    frontend_package = _generated_package_for_frontend(post_id, package)
    PUBLIC_POST_STORE[post_id] = {
        "post_id": post_id,
        "company_id": payload.company_id,
        "status": "generated",
        "generated_package_json": frontend_package,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    return {"post_id": post_id, "status": "generated", "estimated_ready_seconds": 1}


@router.get("/v1/posts/{post_id}")
async def public_get_post(post_id: str) -> dict[str, Any]:
    record = PUBLIC_POST_STORE.get(post_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post_id": record["post_id"],
        "status": record["status"],
        "generated_package_json": record["generated_package_json"],
    }


@router.post("/v1/posts/drafts")
async def public_save_draft(payload: PublicSaveDraftRequest) -> dict[str, Any]:
    post_id = str(uuid4())
    platform = _normalize_public_platform(payload.platform)
    PUBLIC_POST_STORE[post_id] = {
        "post_id": post_id,
        "company_id": payload.company_id,
        "status": "draft",
        "generated_package_json": _draft_package_for_frontend(post_id, platform, payload.content),
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "metadata": {
            "intent": payload.intent,
            "campaign_tag": payload.campaign_tag,
            "topic": payload.topic,
            "tone": payload.tone,
            "cta": payload.cta,
        },
    }
    return {
        "post_id": post_id,
        "status": "draft",
        "platform": platform,
        "created_at": PUBLIC_POST_STORE[post_id]["created_at"],
    }


@router.get("/v1/companies/{company_id}/posts")
async def public_list_company_posts(company_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be greater than or equal to 0")
    items = [
        {
            "post_id": record["post_id"],
            "status": record["status"],
            "generated_package_json": record["generated_package_json"],
        }
        for record in PUBLIC_POST_STORE.values()
        if record.get("company_id") == company_id
    ]
    return {"items": items[offset : offset + limit], "count": len(items), "limit": limit, "offset": offset}


@router.post("/v1/schedules")
async def public_create_schedule(payload: PublicScheduleRequest) -> dict[str, Any]:
    if payload.post_id not in PUBLIC_POST_STORE:
        raise HTTPException(status_code=404, detail="Post not found")
    schedule_ids: list[str] = []
    for target in payload.targets:
        schedule_id = str(uuid4())
        PUBLIC_SCHEDULE_STORE[schedule_id] = {
            "id": schedule_id,
            "schedule_id": schedule_id,
            "post_id": payload.post_id,
            "company_id": payload.company_id,
            "platform": _normalize_public_platform(target.platform),
            "run_at_utc": target.run_at_utc,
            "status": "queued",
            "approval_mode": payload.approval_mode,
            "external_scheduling_status": "not_implemented",
        }
        schedule_ids.append(schedule_id)
    return {"schedule_ids": schedule_ids, "status": "queued"}


@router.get("/v1/schedules/{schedule_id}")
async def public_get_schedule(schedule_id: str) -> dict[str, Any]:
    record = PUBLIC_SCHEDULE_STORE.get(schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return record


@router.post("/v1/schedules/{schedule_id}/approve")
async def public_approve_schedule(schedule_id: str, payload: PublicScheduleApprovalRequest | None = None) -> dict[str, Any]:
    record = PUBLIC_SCHEDULE_STORE.get(schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    record["status"] = "queued"
    record["approved_at"] = datetime.now(tz=timezone.utc).isoformat()
    record["approved_by"] = payload.approved_by if payload else None
    return {
        "approved": True,
        "schedule_id": schedule_id,
        "status": record["status"],
        "approved_at": record["approved_at"],
        "approved_by": record["approved_by"],
    }
