from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response

from ai.schemas.brand import BrandProfile, validate_brand_profile_completeness
from api.dependencies import WorkspaceContext, get_app_settings, get_product_repository, get_workspace_context
from api.schemas.product import (
    BrandProfileRecord,
    BrandProfileUpdate,
    CalendarCreate,
    CalendarPage,
    CalendarUpdate,
    CapabilitiesResponse,
    CapabilityStatus,
    ContentPage,
    PageMeta,
    SessionResponse,
)
from core.config import AppSettings
from core.errors import APIError
from repositories import ProductRepository


router = APIRouter(prefix="/v1", tags=["product"])


def _brand_record(row: dict[str, Any]) -> BrandProfileRecord:
    profile = BrandProfile.model_validate(row["brand_profile_json"])
    return BrandProfileRecord(
        profile=profile,
        validation=validate_brand_profile_completeness(profile),
        profile_version=int(row.get("profile_version") or 1),
        updated_at=row.get("updated_at"),
    )


@router.get("/session", response_model=SessionResponse)
async def session(context: WorkspaceContext = Depends(get_workspace_context)) -> SessionResponse:
    return SessionResponse(**context.model_dump())


@router.get("/brands/{brand_id}/profile", response_model=BrandProfileRecord)
async def get_brand_profile(
    brand_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> BrandProfileRecord:
    row = await repository.get_brand_profile(context.workspace_id, brand_id)
    if row is None or not row.get("brand_profile_json"):
        raise APIError(404, "BRAND_PROFILE_NOT_FOUND", "Brand Brain has not been configured for this brand.")
    return _brand_record(row)


@router.put("/brands/{brand_id}/profile", response_model=BrandProfileRecord)
async def put_brand_profile(
    brand_id: str,
    payload: BrandProfileUpdate,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> BrandProfileRecord:
    if context.brand_id != brand_id or payload.profile.brand_id != brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    row = await repository.save_brand_profile(
        workspace_id=context.workspace_id,
        brand_id=brand_id,
        brand_name=payload.profile.brand_name,
        profile=payload.profile.model_dump(mode="json"),
        expected_version=payload.expected_version,
    )
    if row is None:
        raise APIError(404, "BRAND_NOT_FOUND", "The brand was not found in this workspace.")
    if row.get("conflict"):
        raise APIError(
            409,
            "BRAND_PROFILE_VERSION_CONFLICT",
            "Brand Brain changed since it was loaded.",
            details={"current_version": row["profile_version"]},
        )
    return _brand_record(row)


@router.post("/brands/{brand_id}/profile/validate", response_model=BrandProfileRecord)
async def validate_brand_profile(
    brand_id: str,
    payload: BrandProfileUpdate,
    context: WorkspaceContext = Depends(get_workspace_context),
) -> BrandProfileRecord:
    if context.brand_id != brand_id or payload.profile.brand_id != brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    return BrandProfileRecord(
        profile=payload.profile,
        validation=validate_brand_profile_completeness(payload.profile),
        profile_version=payload.expected_version or 0,
    )


@router.get("/content", response_model=ContentPage)
async def list_content(
    search: str | None = None,
    platform: str | None = None,
    generation_status: str | None = None,
    approval_status: str | None = None,
    campaign: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "created_at",
    order: str = "desc",
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ContentPage:
    items, total = await repository.list_content(
        workspace_id=context.workspace_id,
        search=search,
        platform=platform,
        generation_status=generation_status,
        approval_status=approval_status,
        campaign=campaign,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return ContentPage(items=items, page=PageMeta(total=total, limit=limit, offset=offset))


@router.get("/calendar/items", response_model=CalendarPage)
async def list_calendar(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    platform: str | None = None,
    planning_state: str | None = None,
    approval_status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> CalendarPage:
    items, total = await repository.list_calendar_items(
        workspace_id=context.workspace_id,
        date_from=date_from,
        date_to=date_to,
        platform=platform,
        planning_state=planning_state,
        approval_status=approval_status,
        limit=limit,
        offset=offset,
    )
    return CalendarPage(items=items, page=PageMeta(total=total, limit=limit, offset=offset))


@router.get("/calendar/unscheduled", response_model=ContentPage)
async def list_unscheduled(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ContentPage:
    items, total = await repository.list_unscheduled_content(context.workspace_id, limit, offset)
    return ContentPage(items=items, page=PageMeta(total=total, limit=limit, offset=offset))


@router.post("/calendar/items", response_model=dict[str, Any], status_code=201)
async def create_calendar_item(
    payload: CalendarCreate,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    if context.brand_id is None:
        raise APIError(409, "BRAND_REQUIRED", "This workspace has no active brand.")
    row = await repository.create_calendar_item(
        workspace_id=context.workspace_id,
        brand_id=context.brand_id,
        content_draft_id=payload.content_draft_id,
        platform=payload.platform,
        planned_at=payload.planned_at,
        timezone=payload.timezone,
    )
    if row is None:
        raise APIError(404, "CONTENT_NOT_FOUND", "Content was not found in this workspace.")
    return row


@router.patch("/calendar/items/{item_id}", response_model=dict[str, Any])
async def update_calendar_item(
    item_id: str,
    payload: CalendarUpdate,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    row = await repository.update_calendar_item(
        workspace_id=context.workspace_id,
        item_id=item_id,
        planned_at=payload.planned_at,
        timezone=payload.timezone,
        planning_state=payload.planning_state,
    )
    if row is None:
        raise APIError(404, "CALENDAR_ITEM_NOT_FOUND", "Calendar item was not found in this workspace.")
    return row


@router.delete("/calendar/items/{item_id}", status_code=204)
async def delete_calendar_item(
    item_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> Response:
    if not await repository.delete_calendar_item(context.workspace_id, item_id):
        raise APIError(404, "CALENDAR_ITEM_NOT_FOUND", "Calendar item was not found in this workspace.")
    return Response(status_code=204)


@router.get("/overview", response_model=dict[str, Any])
async def overview(
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    data = await repository.overview(context.workspace_id)
    return {**data, "source": "internal_operational_data", "workspace_timezone": context.timezone}


@router.get("/insights", response_model=dict[str, Any])
async def insights(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> dict[str, Any]:
    data = await repository.insights(context.workspace_id, date_from, date_to)
    return {
        "source": "internal_operational_data",
        "external_analytics": {"status": "Unavailable", "reason": "No platform analytics integration is configured."},
        "metrics": data,
    }


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(
    request: Request,
    settings: AppSettings = Depends(get_app_settings),
    _context: WorkspaceContext = Depends(get_workspace_context),
) -> CapabilitiesResponse:
    database_available = getattr(request.app.state, "db_pool", None) is not None
    ai_live = not settings.AI_MOCK_MODE and bool(os.environ.get("OPENAI_API_KEY"))
    return CapabilitiesResponse(
        database=CapabilityStatus(status="Available" if database_available else "Unavailable", detail="PostgreSQL persistence pool."),
        authentication=CapabilityStatus(status="Configured" if settings.JWT_SECRET else "Unavailable", detail="Signed bearer-token verification."),
        ai_provider=CapabilityStatus(status="Configured" if ai_live else "Unavailable", detail="Central backend OpenAI gateway."),
        ai_mock_mode=CapabilityStatus(
            status="Demo" if settings.AI_MOCK_MODE else "Unavailable",
            detail="Explicit deterministic AI mode is enabled." if settings.AI_MOCK_MODE else "Mock mode is disabled.",
        ),
        media_storage=CapabilityStatus(status="Unavailable", detail="No verified media upload and retrieval service."),
        external_scheduling=CapabilityStatus(status="Unavailable", detail="Calendar stores internal plans only."),
        publishing=CapabilityStatus(status="Unavailable", detail="No platform publishing adapter is connected."),
        external_analytics=CapabilityStatus(status="Unavailable", detail="No platform analytics ingestion is connected."),
        background_workers=CapabilityStatus(status="Unavailable", detail="No required worker is deployed for the MVP."),
    )


@router.get("/audit", response_model=list[dict[str, Any]])
async def audit(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> list[dict[str, Any]]:
    return await repository.list_audit(context.workspace_id, limit, offset)
