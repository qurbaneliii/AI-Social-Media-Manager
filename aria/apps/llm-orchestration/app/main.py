from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

import httpx
import redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sqlalchemy import create_engine

from ai.agents import AIOrchestrator
from ai.approval import (
    ApprovalAction,
    ApprovalDecision,
    ApprovalObjectType,
    ApprovalResult,
    ApprovalStatus,
    DraftNotFoundError,
    InvalidApprovalTransitionError,
)
from ai.approval.queue import (
    ApprovalAuditEventResponse,
    ApprovalDetail,
    ApprovalQueueResponse,
    CalendarDraftDetail,
    CalendarApprovalQueueResponse,
    CommunityApprovalQueueResponse,
    CommunityReplyDraftDetail,
    ContentDraftDetail,
    ContentApprovalQueueResponse,
    DraftListFilters,
    ReportDraftDetail,
    ReportApprovalQueueResponse,
    calendar_detail_from_row,
    calendar_queue_item_from_row,
    community_detail_from_row,
    community_queue_item_from_row,
    content_detail_from_row,
    content_queue_item_from_row,
    report_detail_from_row,
    report_queue_item_from_row,
)
from ai.approval.service import ApprovalService
from ai.llm import LLMClient, LLMSettings
from ai.memory import BrandProfileNotFoundError
from ai.persistence import AIPersistenceRepository
from ai.schemas.analytics import ReportingInsightReport, ReportingInsightRequest
from ai.schemas.brand import (
    BrandProfile,
    BrandProfileResponse,
    BrandProfileValidationResult,
    ProductContext,
    validate_brand_profile_completeness,
)
from ai.schemas.calendar import CalendarPlanningRequest, ContentCalendarPlan
from ai.schemas.community import CommunityManagementRequest, CommunityMessageAnalysis
from ai.schemas.competitor import CompetitorAnalysisRequest, CompetitorInsightReport
from ai.schemas.content import ContentRequest, GeneratedContentPackage, PlatformContext
from ai.schemas.evaluation import AIQualityReview
from ai.schemas.hashtag import HashtagRecommendation, HashtagRecommendationRequest
from ai.schemas.strategy import BrandStrategyPlan, BrandStrategyRequest
from ai.schemas.trend import TrendInsightReport, TrendResearchRequest
from ai.schemas.visual import VisualConceptPackage, VisualConceptRequest


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class CaptionVariant(BaseModel):
    platform: str
    caption_text: str
    hashtags: list[str]
    score: float


class CaptionRequest(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    post_intent: str
    core_message: str
    target_platforms: list[str]
    tone_fingerprint: dict[str, Any] = Field(default_factory=dict)
    visual_profile: dict[str, Any] = Field(default_factory=dict)


class CaptionResponse(BaseModel):
    variants: list[CaptionVariant]


class OrchestrateRequest(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    post_intent: str
    core_message: str
    target_platforms: list[str]
    keywords: list[str] = Field(default_factory=list)
    persona_summary: str = ""
    image_url: str


class OrchestrateResponse(BaseModel):
    context_snapshot: dict[str, Any]
    module_results: dict[str, Any]
    generated_package: dict[str, Any]


class ApprovalActionRequest(BaseModel):
    object_id: str
    object_type: ApprovalObjectType
    reviewer_id: str | None = None
    reviewer_role: str | None = None
    reason: str = ""
    requested_changes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DraftListResponse(ApprovalQueueResponse):
    pass


class BrandProfileUpsertRequest(BaseModel):
    profile: BrandProfile


class BrandProfileValidationRequest(BaseModel):
    profile: BrandProfile
    using_default_context: bool = False


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


class ContentRefinementRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    instruction: str = Field(min_length=1, max_length=500)


class ContentRefinementResponse(BaseModel):
    improved: str
    mock_mode: bool = True
    route: str = "/internal/ai/content/refine"


PUBLIC_POST_STORE: dict[str, dict[str, Any]] = {}
PUBLIC_SCHEDULE_STORE: dict[str, dict[str, Any]] = {}


def _get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        parsed = [origin.strip() for origin in raw.split(",") if origin.strip()]
        if parsed:
            return parsed
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


class LiteLLMAdapter:
    def __init__(self, provider_keys: dict[str, str | None]) -> None:
        self.provider_keys = provider_keys

    async def chat(self, provider: str, model: str, messages: list[Message], response_format: str = "json") -> dict[str, Any]:
        key = self.provider_keys.get(provider)
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])

        if key:
            raise RuntimeError("Legacy LiteLLMAdapter is demo-only and must not handle configured provider keys.")
        return {
            "provider_used": "demo",
            "model_used": model,
            "output": {
                "summary": prompt[:200],
                "variants": 3,
            }
            if response_format == "json"
            else prompt[:200],
            "mock_mode": True,
            "token_usage": None,
        }


class Dependencies:
    def __init__(self) -> None:
        database_url = os.getenv("LEGACY_SQLALCHEMY_DATABASE_URL") or "sqlite+pysqlite:///:memory:"
        redis_url = os.getenv("LEGACY_REDIS_URL", "redis://localhost:6379/0")
        self.db = create_engine(database_url, pool_pre_ping=True)
        self.cache = redis.Redis.from_url(redis_url)
        self.vector = self.db
        self.adapter = LiteLLMAdapter(
            {
                "openai": None,
                "anthropic": None,
                "mistral": None,
                "deepseek": None,
            }
        )


def get_deps() -> Dependencies:
    return Dependencies()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    app.state.db_pool = None
    if database_url:
        import asyncpg

        app.state.db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    try:
        yield
    finally:
        db_pool = getattr(app.state, "db_pool", None)
        if db_pool is not None:
            await db_pool.close()


app = FastAPI(title="ARIA LLM Orchestration Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app)


@app.exception_handler(BrandProfileNotFoundError)
async def brand_profile_not_found_handler(request: Request, exc: BrandProfileNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DraftNotFoundError)
async def draft_not_found_handler(request: Request, exc: DraftNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "object_type": exc.object_type, "object_id": exc.object_id},
    )


@app.exception_handler(InvalidApprovalTransitionError)
async def invalid_approval_transition_handler(request: Request, exc: InvalidApprovalTransitionError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
            "object_type": exc.object_type,
            "previous_status": exc.previous_status,
            "new_status": exc.new_status,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-orchestration"}


@app.get("/internal/ai/workspace-context", response_model=ProductContext)
def ai_get_workspace_context() -> ProductContext:
    return ProductContext()


def get_ai_orchestrator(request: Request) -> AIOrchestrator:
    db_pool = getattr(request.app.state, "db_pool", None)
    persistence_repository = AIPersistenceRepository(db_pool) if db_pool is not None else None
    return AIOrchestrator(
        llm_client=LLMClient(LLMSettings()),
        persistence_repository=persistence_repository,
    )


def get_persistence_repository(request: Request) -> AIPersistenceRepository:
    db_pool = getattr(request.app.state, "db_pool", None)
    if db_pool is None:
        raise HTTPException(status_code=503, detail="AI persistence database pool is not configured.")
    return AIPersistenceRepository(db_pool)


def get_approval_service(repository: AIPersistenceRepository = Depends(get_persistence_repository)) -> ApprovalService:
    return ApprovalService(repository)


def _brand_profile_response(profile: BrandProfile, *, persisted: bool = True) -> BrandProfileResponse:
    return BrandProfileResponse(
        profile=profile,
        validation=validate_brand_profile_completeness(profile),
        persisted=persisted,
    )


@app.get("/internal/ai/brand-profile/{brand_id}", response_model=BrandProfileResponse)
async def ai_get_brand_profile(
    brand_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    profile = await repository.load_brand_profile(brand_id)
    if profile is None:
        raise BrandProfileNotFoundError(brand_id)
    return _brand_profile_response(profile)


@app.post("/internal/ai/brand-profile", response_model=BrandProfileResponse)
async def ai_upsert_brand_profile(
    payload: BrandProfileUpsertRequest,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    await repository.save_brand_profile(payload.profile)
    return _brand_profile_response(payload.profile)


@app.put("/internal/ai/brand-profile/{brand_id}", response_model=BrandProfileResponse)
async def ai_update_brand_profile(
    brand_id: str,
    payload: BrandProfileUpsertRequest,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    if payload.profile.brand_id != brand_id:
        raise HTTPException(status_code=400, detail="brand_id path parameter must match profile.brand_id.")
    await repository.save_brand_profile(payload.profile)
    return _brand_profile_response(payload.profile)


@app.post("/internal/ai/brand-profile/validate", response_model=BrandProfileValidationResult)
async def ai_validate_brand_profile(payload: BrandProfileValidationRequest) -> BrandProfileValidationResult:
    return validate_brand_profile_completeness(
        payload.profile,
        using_default_context=payload.using_default_context,
    )


async def _apply_approval_action(
    payload: ApprovalActionRequest,
    action: ApprovalAction,
    new_status: ApprovalStatus,
    service: ApprovalService,
) -> ApprovalResult:
    decision = ApprovalDecision(
        object_id=payload.object_id,
        object_type=payload.object_type,
        new_status=new_status,
        action=action,
        reviewer_id=payload.reviewer_id,
        reviewer_role=payload.reviewer_role,
        reason=payload.reason,
        requested_changes=payload.requested_changes,
        metadata=payload.metadata,
    )
    return await service.apply_decision(decision)


def _queue_filters(
    *,
    brand_id: str | None = None,
    status: str | None = None,
    object_type: ApprovalObjectType | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> DraftListFilters:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be greater than or equal to 0")
    if created_after and created_before and created_after > created_before:
        raise HTTPException(status_code=400, detail="created_after must be before created_before")
    return DraftListFilters(
        brand_id=brand_id,
        status=status,
        object_type=object_type,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )


VALID_APPROVAL_STATUSES_BY_TYPE: dict[ApprovalObjectType, set[str]] = {
    ApprovalObjectType.CONTENT_DRAFT: {"draft", "in_review", "approved", "rejected", "changes_requested", "archived"},
    ApprovalObjectType.CALENDAR_DRAFT: {
        "draft",
        "in_review",
        "approved",
        "rejected",
        "changes_requested",
        "ready_for_scheduling",
        "archived",
    },
    ApprovalObjectType.COMMUNITY_REPLY: {
        "draft",
        "in_review",
        "approved",
        "rejected",
        "changes_requested",
        "escalated",
        "archived",
    },
    ApprovalObjectType.REPORT_DRAFT: {"draft", "in_review", "approved", "rejected", "changes_requested", "archived"},
}


def _status_matches_queue(object_type: ApprovalObjectType, status: str | None) -> bool:
    return status is None or status in VALID_APPROVAL_STATUSES_BY_TYPE[object_type]


def _validate_status_for_queue(object_type: ApprovalObjectType, status: str | None) -> None:
    if not _status_matches_queue(object_type, status):
        raise HTTPException(status_code=400, detail=f"Invalid status for {object_type.value}: {status}")


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


async def _approval_detail_for_object(
    object_type: ApprovalObjectType,
    object_id: str,
    repository: AIPersistenceRepository,
    service: ApprovalService,
) -> ApprovalDetail:
    events = await service.list_audit_events(object_type, object_id)
    if object_type == ApprovalObjectType.CONTENT_DRAFT:
        row = await repository.get_content_draft_by_id(object_id)
        if row is None:
            raise DraftNotFoundError(object_type.value, object_id)
        return content_detail_from_row(row, events)
    if object_type == ApprovalObjectType.CALENDAR_DRAFT:
        row = await repository.get_calendar_draft_item_by_id(object_id)
        if row is None:
            raise DraftNotFoundError(object_type.value, object_id)
        return calendar_detail_from_row(row, events)
    if object_type == ApprovalObjectType.COMMUNITY_REPLY:
        row = await repository.get_community_reply_draft_by_id(object_id)
        if row is None:
            raise DraftNotFoundError(object_type.value, object_id)
        return community_detail_from_row(row, events)
    if object_type == ApprovalObjectType.REPORT_DRAFT:
        row = await repository.get_report_draft_by_id(object_id)
        if row is None:
            raise DraftNotFoundError(object_type.value, object_id)
        return report_detail_from_row(row, events)
    raise HTTPException(status_code=400, detail=f"Invalid approval object type: {object_type}")


@app.post("/internal/ai/generate-content-package", response_model=GeneratedContentPackage)
async def ai_generate_content_package(
    payload: ContentRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> GeneratedContentPackage:
    return await orchestrator.generate_content_package(payload)


@app.post("/internal/ai/content/refine", response_model=ContentRefinementResponse)
async def ai_refine_content(payload: ContentRefinementRequest) -> ContentRefinementResponse:
    improved = f"{payload.content.strip()}\n\nRefinement note: {payload.instruction.strip()}"
    return ContentRefinementResponse(improved=improved)


@app.post("/v1/posts/generate")
async def public_generate_post(
    payload: PublicGeneratePostRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> dict[str, Any]:
    platform = _normalize_public_platform(payload.target_platforms[0])
    post_id = str(uuid4())
    brand_profile = _public_brand_profile(payload.company_id, [_normalize_public_platform(item) for item in payload.target_platforms], topic=payload.core_message)
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


@app.get("/v1/posts/{post_id}")
async def public_get_post(post_id: str) -> dict[str, Any]:
    record = PUBLIC_POST_STORE.get(post_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post_id": record["post_id"],
        "status": record["status"],
        "generated_package_json": record["generated_package_json"],
    }


@app.post("/v1/posts/drafts")
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


@app.get("/v1/companies/{company_id}/posts")
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


@app.post("/v1/schedules")
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


@app.get("/v1/schedules/{schedule_id}")
async def public_get_schedule(schedule_id: str) -> dict[str, Any]:
    record = PUBLIC_SCHEDULE_STORE.get(schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return record


@app.post("/v1/schedules/{schedule_id}/approve")
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


@app.post("/internal/ai/brand-strategy", response_model=BrandStrategyPlan)
async def ai_create_brand_strategy(
    payload: BrandStrategyRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> BrandStrategyPlan:
    return await orchestrator.create_brand_strategy(payload)


@app.post("/internal/ai/competitors/analyze", response_model=CompetitorInsightReport)
async def ai_analyze_competitors(
    payload: CompetitorAnalysisRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> CompetitorInsightReport:
    return await orchestrator.analyze_competitors(payload)


@app.post("/internal/ai/trends/research", response_model=TrendInsightReport)
async def ai_research_trends(
    payload: TrendResearchRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> TrendInsightReport:
    return await orchestrator.research_trends(payload)


@app.post("/internal/ai/hashtags/recommend", response_model=HashtagRecommendation)
async def ai_recommend_hashtags(
    payload: HashtagRecommendationRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> HashtagRecommendation:
    return await orchestrator.recommend_hashtags(payload)


@app.post("/internal/ai/visual-concept", response_model=VisualConceptPackage)
async def ai_generate_visual_concept(
    payload: VisualConceptRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> VisualConceptPackage:
    return await orchestrator.generate_visual_concept(payload)


@app.post("/internal/ai/content-calendar", response_model=ContentCalendarPlan)
async def ai_create_content_calendar(
    payload: CalendarPlanningRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> ContentCalendarPlan:
    return await orchestrator.create_content_calendar(payload)


@app.post("/internal/ai/community/analyze", response_model=CommunityMessageAnalysis)
async def ai_analyze_community_message(
    payload: CommunityManagementRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> CommunityMessageAnalysis:
    analysis = await orchestrator.analyze_community_message(payload)
    if orchestrator.persistence_repository is not None:
        await orchestrator.persistence_repository.save_community_reply_draft(
            brand_id=payload.brand_profile.brand_id,
            analysis=analysis,
            metadata={
                "platform": payload.platform,
                "author_context": payload.author_context,
                "conversation_context": payload.conversation_context,
                "phase": "phase_4_approval_lifecycle",
            },
        )
    return analysis


@app.post("/internal/ai/reports/insights", response_model=ReportingInsightReport)
async def ai_generate_report_insights(
    payload: ReportingInsightRequest,
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> ReportingInsightReport:
    return await orchestrator.generate_report_insights(payload)


@app.post("/internal/ai/content-quality/review", response_model=AIQualityReview)
async def ai_review_content_quality(
    payload: dict[str, Any],
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator),
) -> AIQualityReview:
    return await orchestrator.review_content_quality(
        payload.get("request", {}),
        payload.get("package", payload.get("output", {})),
    )


@app.post("/internal/ai/approval/decision", response_model=ApprovalResult)
async def ai_apply_approval_decision(
    payload: ApprovalDecision,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await service.apply_decision(payload)


@app.post("/internal/ai/approval/submit", response_model=ApprovalResult)
async def ai_submit_for_approval(
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await _apply_approval_action(payload, ApprovalAction.SUBMIT, ApprovalStatus.IN_REVIEW, service)


@app.post("/internal/ai/approval/approve", response_model=ApprovalResult)
async def ai_approve_draft(
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await _apply_approval_action(payload, ApprovalAction.APPROVE, ApprovalStatus.APPROVED, service)


@app.post("/internal/ai/approval/reject", response_model=ApprovalResult)
async def ai_reject_draft(
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await _apply_approval_action(payload, ApprovalAction.REJECT, ApprovalStatus.REJECTED, service)


@app.post("/internal/ai/approval/request-changes", response_model=ApprovalResult)
async def ai_request_changes(
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await _apply_approval_action(
        payload,
        ApprovalAction.REQUEST_CHANGES,
        ApprovalStatus.CHANGES_REQUESTED,
        service,
    )


@app.post("/internal/ai/approval/archive", response_model=ApprovalResult)
async def ai_archive_draft(
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalResult:
    return await _apply_approval_action(payload, ApprovalAction.ARCHIVE, ApprovalStatus.ARCHIVED, service)


@app.get("/internal/ai/approval/audit/{object_type}/{object_id}", response_model=list[ApprovalAuditEventResponse])
async def ai_list_approval_audit_events(
    object_type: ApprovalObjectType,
    object_id: str,
    service: ApprovalService = Depends(get_approval_service),
) -> list[ApprovalAuditEventResponse]:
    return await service.list_audit_events(object_type, object_id)


@app.get("/internal/ai/approval/detail/content/{draft_id}", response_model=ContentDraftDetail)
async def ai_get_content_draft_detail(
    draft_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
    service: ApprovalService = Depends(get_approval_service),
) -> ContentDraftDetail:
    detail = await _approval_detail_for_object(ApprovalObjectType.CONTENT_DRAFT, draft_id, repository, service)
    return detail  # type: ignore[return-value]


@app.get("/internal/ai/approval/detail/calendar/{item_id}", response_model=CalendarDraftDetail)
async def ai_get_calendar_draft_detail(
    item_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
    service: ApprovalService = Depends(get_approval_service),
) -> CalendarDraftDetail:
    detail = await _approval_detail_for_object(ApprovalObjectType.CALENDAR_DRAFT, item_id, repository, service)
    return detail  # type: ignore[return-value]


@app.get("/internal/ai/approval/detail/community/{reply_draft_id}", response_model=CommunityReplyDraftDetail)
async def ai_get_community_reply_detail(
    reply_draft_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
    service: ApprovalService = Depends(get_approval_service),
) -> CommunityReplyDraftDetail:
    detail = await _approval_detail_for_object(ApprovalObjectType.COMMUNITY_REPLY, reply_draft_id, repository, service)
    return detail  # type: ignore[return-value]


@app.get("/internal/ai/approval/detail/reports/{report_id}", response_model=ReportDraftDetail)
async def ai_get_report_draft_detail(
    report_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
    service: ApprovalService = Depends(get_approval_service),
) -> ReportDraftDetail:
    detail = await _approval_detail_for_object(ApprovalObjectType.REPORT_DRAFT, report_id, repository, service)
    return detail  # type: ignore[return-value]


@app.get("/internal/ai/approval/detail/{object_type}/{object_id}", response_model=ApprovalDetail)
async def ai_get_approval_detail(
    object_type: str,
    object_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalDetail:
    try:
        parsed_type = ApprovalObjectType(object_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid approval object type: {object_type}") from exc
    return await _approval_detail_for_object(parsed_type, object_id, repository, service)


@app.get("/internal/ai/approval/queue/content", response_model=ContentApprovalQueueResponse)
async def ai_list_content_approval_queue(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> ContentApprovalQueueResponse:
    filters = _queue_filters(
        brand_id=brand_id,
        status=status,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )
    _validate_status_for_queue(ApprovalObjectType.CONTENT_DRAFT, filters.status)
    rows = await repository.list_content_drafts(
        brand_id=filters.brand_id,
        status=filters.status,
        platform=filters.platform,
        limit=filters.limit,
        offset=filters.offset,
        created_after=filters.created_after,
        created_before=filters.created_before,
    )
    items = [content_queue_item_from_row(row) for row in rows]
    return ContentApprovalQueueResponse(items=items, count=len(items), limit=filters.limit, offset=filters.offset)


@app.get("/internal/ai/approval/queue/calendar", response_model=CalendarApprovalQueueResponse)
async def ai_list_calendar_approval_queue(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> CalendarApprovalQueueResponse:
    filters = _queue_filters(
        brand_id=brand_id,
        status=status,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )
    _validate_status_for_queue(ApprovalObjectType.CALENDAR_DRAFT, filters.status)
    rows = await repository.list_calendar_drafts(
        brand_id=filters.brand_id,
        status=filters.status,
        platform=filters.platform,
        limit=filters.limit,
        offset=filters.offset,
        created_after=filters.created_after,
        created_before=filters.created_before,
    )
    items = [calendar_queue_item_from_row(row) for row in rows]
    return CalendarApprovalQueueResponse(items=items, count=len(items), limit=filters.limit, offset=filters.offset)


@app.get("/internal/ai/approval/queue/community", response_model=CommunityApprovalQueueResponse)
async def ai_list_community_approval_queue(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> CommunityApprovalQueueResponse:
    filters = _queue_filters(
        brand_id=brand_id,
        status=status,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )
    _validate_status_for_queue(ApprovalObjectType.COMMUNITY_REPLY, filters.status)
    rows = await repository.list_community_reply_drafts(
        brand_id=filters.brand_id,
        status=filters.status,
        platform=filters.platform,
        limit=filters.limit,
        offset=filters.offset,
        created_after=filters.created_after,
        created_before=filters.created_before,
    )
    items = [community_queue_item_from_row(row) for row in rows]
    return CommunityApprovalQueueResponse(items=items, count=len(items), limit=filters.limit, offset=filters.offset)


@app.get("/internal/ai/approval/queue/reports", response_model=ReportApprovalQueueResponse)
async def ai_list_report_approval_queue(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> ReportApprovalQueueResponse:
    filters = _queue_filters(
        brand_id=brand_id,
        status=status,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )
    _validate_status_for_queue(ApprovalObjectType.REPORT_DRAFT, filters.status)
    rows = await repository.list_report_drafts(
        brand_id=filters.brand_id,
        status=filters.status,
        platform=filters.platform,
        limit=filters.limit,
        offset=filters.offset,
        created_after=filters.created_after,
        created_before=filters.created_before,
    )
    items = [report_queue_item_from_row(row) for row in rows]
    return ReportApprovalQueueResponse(items=items, count=len(items), limit=filters.limit, offset=filters.offset)


@app.get("/internal/ai/approval/queue", response_model=ApprovalQueueResponse)
async def ai_list_approval_queue(
    brand_id: str | None = None,
    status: str | None = None,
    object_type: ApprovalObjectType | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> ApprovalQueueResponse:
    filters = _queue_filters(
        brand_id=brand_id,
        status=status,
        object_type=object_type,
        platform=platform,
        limit=limit,
        offset=offset,
        created_after=created_after,
        created_before=created_before,
    )
    object_types = [filters.object_type] if filters.object_type else list(ApprovalObjectType)
    if filters.object_type:
        _validate_status_for_queue(filters.object_type, filters.status)
    else:
        object_types = [queue_type for queue_type in object_types if _status_matches_queue(queue_type, filters.status)]
        if not object_types:
            raise HTTPException(status_code=400, detail=f"Invalid status for every approval object type: {filters.status}")

    items: list[Any] = []
    page_fetch_limit = filters.offset + filters.limit
    for queue_type in object_types:
        if queue_type == ApprovalObjectType.CONTENT_DRAFT:
            rows = await repository.list_content_drafts(filters.brand_id, filters.status, filters.platform, page_fetch_limit, 0, filters.created_after, filters.created_before)
            items.extend(content_queue_item_from_row(row) for row in rows)
        elif queue_type == ApprovalObjectType.CALENDAR_DRAFT:
            rows = await repository.list_calendar_drafts(filters.brand_id, filters.status, filters.platform, page_fetch_limit, 0, filters.created_after, filters.created_before)
            items.extend(calendar_queue_item_from_row(row) for row in rows)
        elif queue_type == ApprovalObjectType.COMMUNITY_REPLY:
            rows = await repository.list_community_reply_drafts(filters.brand_id, filters.status, filters.platform, page_fetch_limit, 0, filters.created_after, filters.created_before)
            items.extend(community_queue_item_from_row(row) for row in rows)
        elif queue_type == ApprovalObjectType.REPORT_DRAFT:
            rows = await repository.list_report_drafts(filters.brand_id, filters.status, filters.platform, page_fetch_limit, 0, filters.created_after, filters.created_before)
            items.extend(report_queue_item_from_row(row) for row in rows)
    items.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    total_visible = len(items)
    page = items[filters.offset : filters.offset + filters.limit]
    return ApprovalQueueResponse(items=page, count=total_visible, limit=filters.limit, offset=filters.offset)


@app.get("/internal/ai/drafts/content", response_model=ContentApprovalQueueResponse)
async def ai_list_content_drafts(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> ContentApprovalQueueResponse:
    return await ai_list_content_approval_queue(
        brand_id,
        status,
        platform,
        limit,
        offset,
        created_after,
        created_before,
        repository,
    )


@app.get("/internal/ai/drafts/calendar", response_model=CalendarApprovalQueueResponse)
async def ai_list_calendar_drafts(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> CalendarApprovalQueueResponse:
    return await ai_list_calendar_approval_queue(
        brand_id,
        status,
        platform,
        limit,
        offset,
        created_after,
        created_before,
        repository,
    )


@app.get("/internal/ai/drafts/community", response_model=CommunityApprovalQueueResponse)
async def ai_list_community_reply_drafts(
    brand_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> CommunityApprovalQueueResponse:
    return await ai_list_community_approval_queue(
        brand_id,
        status,
        platform,
        limit,
        offset,
        created_after,
        created_before,
        repository,
    )


@app.post("/internal/captions/generate", response_model=CaptionResponse)
async def caption_generate(
    payload: CaptionRequest,
    response: Response,
    deps: Dependencies = Depends(get_deps),
) -> CaptionResponse:
    response.headers["x-aria-deprecated-route"] = "legacy-caption-generator"
    response.headers["x-aria-demo-mode"] = "true"
    variants: list[CaptionVariant] = []

    for platform in payload.target_platforms:
        base_system = Message(role="system", content="You generate concise social media captions in structured style.")
        base_user = Message(
            role="user",
            content=(
                f"Platform={platform}; intent={payload.post_intent}; message={payload.core_message}; "
                f"tone={payload.tone_fingerprint}; visual={payload.visual_profile}"
            ),
        )

        await deps.adapter.chat("openai", "gpt-4o-mini", [base_system, base_user], response_format="json")
        seed = len(platform) + len(payload.core_message)
        for i in range(3):
            caption = f"{payload.core_message} | {platform} variant {i + 1}"
            hashtags = [f"#{platform}", "#ai", "#socialmedia", f"#v{i + 1}"]
            score = round(min(0.99, 0.6 + ((seed % 10) / 100) + (0.05 * i)), 4)
            variants.append(CaptionVariant(platform=platform, caption_text=caption, hashtags=hashtags, score=score))

    variants.sort(key=lambda v: (v.platform, -v.score))
    return CaptionResponse(variants=variants)


@app.post("/run", response_model=OrchestrateResponse)
async def orchestrate(
    payload: OrchestrateRequest,
    response: Response,
    deps: Dependencies = Depends(get_deps),
) -> OrchestrateResponse:
    response.headers["x-aria-deprecated-route"] = "legacy-orchestration-run"
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        content_req = client.post(
            "http://content-analysis:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "documents": [payload.core_message],
                "engagement_scores": [0.1, 0.2, 0.3],
            },
        )
        visual_req = client.post(
            "http://visual-understanding:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "media_id": payload.post_id,
                "image_url": payload.image_url,
            },
        )
        hashtag_req = client.post(
            "http://hashtag-seo:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "platform": payload.target_platforms[0],
                "keywords": payload.keywords,
                "top_terms": payload.keywords,
            },
        )
        audience_req = client.post(
            "http://audience-targeting:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "segments": ["B2B"],
                "persona_summary": payload.persona_summary,
                "platforms": payload.target_platforms,
            },
        )
        time_req = client.post(
            "http://time-optimization:8000/rank",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "platform": payload.target_platforms[0],
                "timezone_name": "UTC",
                "historical_engagement_by_hour": [0.05] * 24,
            },
        )

        responses = await asyncio.gather(content_req, visual_req, hashtag_req, audience_req, time_req, return_exceptions=True)

    for response in responses:
        if isinstance(response, Exception):
            raise HTTPException(status_code=503, detail=str(response))
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail=response.text)

    content_data = responses[0].json()
    visual_data = responses[1].json()
    hashtag_data = responses[2].json()
    audience_data = responses[3].json()
    time_data = responses[4].json()

    caption_data = await caption_generate(
        CaptionRequest(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            post_id=payload.post_id,
            post_intent=payload.post_intent,
            core_message=payload.core_message,
            target_platforms=payload.target_platforms,
            tone_fingerprint=content_data.get("tone_fingerprint_json", {}),
            visual_profile={"palette": visual_data.get("palette", [])},
        ),
        response,
        deps,
    )
    response.headers["x-aria-deprecated-route"] = "legacy-orchestration-run"

    required_modules = {
        "content_analysis": content_data,
        "visual_understanding": visual_data,
        "hashtag_seo": hashtag_data,
        "audience_targeting": audience_data,
        "time_optimization": time_data,
        "caption_generation": caption_data.model_dump(mode="json"),
    }

    top_variant = max(caption_data.variants, key=lambda v: v.score)
    generated_package = {
        "post_id": payload.post_id,
        "selected_variant": top_variant.model_dump(mode="json"),
        "all_variants": [v.model_dump(mode="json") for v in caption_data.variants],
        "hashtags": hashtag_data.get("hashtags", []),
        "audience": audience_data.get("audience", {}),
        "time_windows": time_data.get("ranked_windows", []),
        "status": "generated",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    context_snapshot = {
        "tone": content_data.get("tone_fingerprint_json", {}),
        "visual": {
            "palette": visual_data.get("palette", []),
            "layout": visual_data.get("layout", {}),
        },
        "platforms": payload.target_platforms,
        "keywords": payload.keywords,
    }

    return OrchestrateResponse(
        context_snapshot=context_snapshot,
        module_results=required_modules,
        generated_package=generated_package,
    )
