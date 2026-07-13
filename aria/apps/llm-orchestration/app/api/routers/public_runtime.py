from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai.agents import AIOrchestrator
from ai.schemas.brand import BrandProfile
from ai.schemas.content import ContentRequest, GeneratedContentPackage, PlatformContext
from api.dependencies import WorkspaceContext, get_ai_orchestrator, get_product_repository, get_workspace_context
from core.errors import APIError
from repositories import ProductRepository


router = APIRouter(tags=["public-runtime"])

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
        raise APIError(400, "UNSUPPORTED_PLATFORM", f"Unsupported platform: {platform}")
    return value


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


@router.post("/v1/posts/generate")
async def public_generate_post(
    payload: PublicGeneratePostRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    if payload.company_id != context.brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    profile_record = await repository.get_brand_profile(context.workspace_id, payload.company_id)
    if profile_record is None or not profile_record.get("brand_profile_json"):
        raise APIError(409, "BRAND_PROFILE_REQUIRED", "Complete and save Brand Brain before generating content.")
    brand_profile = BrandProfile.model_validate(profile_record["brand_profile_json"])
    packages: list[GeneratedContentPackage] = []
    for raw_platform in payload.target_platforms:
        platform = _normalize_public_platform(raw_platform)
        packages.append(
            await orchestrator.generate_content_package(
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
        )
    post_id = await repository.create_content(
        workspace_id=context.workspace_id,
        brand_id=payload.company_id,
        owner_id=context.user_id,
        topic=payload.core_message,
        content_type="post",
        campaign=payload.campaign_tag,
        packages=[package.model_dump(mode="json") for package in packages],
        mock_mode=orchestrator.llm_client.settings.use_mock_mode,
        model=orchestrator.llm_client.settings.openai_model,
        idempotency_key=None,
    )
    return {"post_id": post_id, "status": "generated", "estimated_ready_seconds": 1}


@router.get("/v1/posts/{post_id}")
async def public_get_post(
    post_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    record = await repository.get_content(context.workspace_id, post_id)
    if record is None:
        raise APIError(404, "CONTENT_NOT_FOUND", "Content was not found in this workspace.")
    variants = record.get("variants") or []
    selected = next((item for item in variants if item.get("is_selected")), variants[0] if variants else None)
    package = selected.get("package") if selected else record.get("content_package_json") or {}
    return {
        "post_id": str(record["draft_id"]),
        "status": record["generation_status"],
        "generated_package_json": _generated_package_for_frontend(post_id, GeneratedContentPackage.model_validate(package)),
    }


@router.post("/v1/posts/drafts")
async def public_save_draft(
    payload: PublicSaveDraftRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    if payload.company_id != context.brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    platform = _normalize_public_platform(payload.platform)
    post_id = await repository.save_user_draft(
        workspace_id=context.workspace_id,
        brand_id=payload.company_id,
        owner_id=context.user_id,
        platform=platform,
        content=payload.content,
        topic=payload.topic or payload.intent,
        campaign=payload.campaign_tag,
    )
    return {
        "post_id": post_id,
        "status": "draft",
        "platform": platform,
        "created_at": datetime.now().astimezone().isoformat(),
    }


@router.get("/v1/companies/{company_id}/posts")
async def public_list_company_posts(
    company_id: str,
    limit: int = 50,
    offset: int = 0,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    if company_id != context.brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    if limit < 1 or limit > 100:
        raise APIError(400, "INVALID_PAGE_SIZE", "limit must be between 1 and 100")
    if offset < 0:
        raise APIError(400, "INVALID_OFFSET", "offset must be greater than or equal to 0")
    records, total = await repository.list_content(
        workspace_id=context.workspace_id,
        search=None,
        platform=None,
        generation_status=None,
        approval_status=None,
        campaign=None,
        date_from=None,
        date_to=None,
        sort="created_at",
        order="desc",
        limit=limit,
        offset=offset,
    )
    items = [
        {
            "post_id": str(record["draft_id"]),
            "status": record["generation_status"],
            "generated_package_json": {
                "variants": [
                    {
                        "variant_id": str(variant["variant_id"]),
                        "platform": variant["platform"],
                        "text": variant["content_text"],
                        "scores": variant.get("scores") or {},
                        "provider_used": variant.get("provider") or ("mock" if record.get("mock_mode") else "user"),
                    }
                    for variant in record.get("variants", [])
                ],
                "selected_variant_id": str(record["selected_variant_id"]) if record.get("selected_variant_id") else None,
            },
        }
        for record in records
    ]
    return {"items": items, "count": total, "limit": limit, "offset": offset}


@router.post("/v1/schedules")
async def public_create_schedule(
    payload: PublicScheduleRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    if payload.company_id != context.brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    schedule_ids: list[str] = []
    for target in payload.targets:
        try:
            planned_at = datetime.fromisoformat(target.run_at_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise APIError(422, "INVALID_PLANNED_TIME", "run_at_utc must be an ISO-8601 timestamp.") from exc
        record = await repository.create_calendar_item(
            workspace_id=context.workspace_id,
            brand_id=payload.company_id,
            content_draft_id=payload.post_id,
            platform=_normalize_public_platform(target.platform),
            planned_at=planned_at,
            timezone="UTC",
        )
        if record is None:
            raise APIError(404, "CONTENT_NOT_FOUND", "Content was not found in this workspace.")
        schedule_ids.append(str(record["calendar_item_id"]))
    return {"schedule_ids": schedule_ids, "status": "draft_plan", "external_scheduling": "unavailable"}


@router.get("/v1/schedules/{schedule_id}")
async def public_get_schedule(
    schedule_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    records, _ = await repository.list_calendar_items(
        workspace_id=context.workspace_id,
        date_from=None,
        date_to=None,
        platform=None,
        planning_state=None,
        approval_status=None,
        limit=100,
        offset=0,
    )
    record = next((item for item in records if str(item["calendar_item_id"]) == schedule_id), None)
    if record is None:
        raise APIError(404, "CALENDAR_ITEM_NOT_FOUND", "Calendar item was not found in this workspace.")
    return {
        "id": schedule_id,
        "schedule_id": schedule_id,
        "post_id": str(record["content_draft_id"]),
        "platform": record["platform"],
        "run_at_utc": record["planned_at"],
        "status": record["planning_state"],
        "approval_status": record["approval_status"],
        "external_scheduling_status": "not_implemented",
    }


@router.post("/v1/schedules/{schedule_id}/approve")
async def public_approve_schedule(
    schedule_id: str,
    payload: PublicScheduleApprovalRequest | None = None,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    record = await repository.update_calendar_item(
        workspace_id=context.workspace_id,
        item_id=schedule_id,
        planned_at=None,
        timezone=None,
        planning_state="approved_internal",
    )
    if record is None:
        raise APIError(404, "CALENDAR_ITEM_NOT_FOUND", "Calendar item was not found in this workspace.")
    approved_at = datetime.now().astimezone().isoformat()
    return {
        "approved": True,
        "schedule_id": schedule_id,
        "status": "approved_internal",
        "approved_at": approved_at,
        "approved_by": context.user_id,
        "external_scheduling": "unavailable",
    }
