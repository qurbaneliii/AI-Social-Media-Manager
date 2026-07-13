from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ai.approval import (
    ApprovalAction,
    ApprovalAuditEvent,
    ApprovalDecision,
    ApprovalObjectType,
    ApprovalResult,
    ApprovalStatus,
    InvalidApprovalTransitionError,
)
from ai.approval.queue import (
    ApprovalDetail,
    ApprovalQueueResponse,
    calendar_detail_from_row,
    calendar_queue_item_from_row,
    community_detail_from_row,
    community_queue_item_from_row,
    content_detail_from_row,
    content_queue_item_from_row,
    report_detail_from_row,
    report_queue_item_from_row,
)
from api.dependencies import WorkspaceContext, get_product_repository, get_workspace_context
from core.errors import APIError
from repositories import ProductRepository


router = APIRouter(prefix="/v1/approval", tags=["approval"])


class ApprovalActionRequest(BaseModel):
    object_id: str
    object_type: ApprovalObjectType
    reason: str = ""
    requested_changes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionRequest(ApprovalActionRequest):
    new_status: ApprovalStatus
    action: ApprovalAction


def _queue_item(object_type: str, row: dict[str, Any]) -> Any:
    if object_type == ApprovalObjectType.CONTENT_DRAFT.value:
        return content_queue_item_from_row(row)
    if object_type == ApprovalObjectType.CALENDAR_DRAFT.value:
        return calendar_queue_item_from_row(row)
    if object_type == ApprovalObjectType.COMMUNITY_REPLY.value:
        return community_queue_item_from_row(row)
    return report_queue_item_from_row(row)


def _detail(object_type: ApprovalObjectType, row: dict[str, Any], events: list[ApprovalAuditEvent]) -> ApprovalDetail:
    if object_type == ApprovalObjectType.CONTENT_DRAFT:
        return content_detail_from_row(row, events)
    if object_type == ApprovalObjectType.CALENDAR_DRAFT:
        return calendar_detail_from_row(row, events)
    if object_type == ApprovalObjectType.COMMUNITY_REPLY:
        return community_detail_from_row(row, events)
    return report_detail_from_row(row, events)


def _require_decision_role(context: WorkspaceContext, action: ApprovalAction) -> None:
    if action == ApprovalAction.SUBMIT:
        allowed = {"agency_admin", "brand_manager", "content_creator"}
    else:
        allowed = {"agency_admin", "brand_manager"}
    if context.role not in allowed:
        raise APIError(403, "INSUFFICIENT_ROLE", "The workspace role cannot perform this approval action.")


async def _apply(
    payload: ApprovalDecisionRequest,
    repository: ProductRepository,
    context: WorkspaceContext,
) -> ApprovalResult:
    _require_decision_role(context, payload.action)
    try:
        result = await repository.apply_approval_decision(
            workspace_id=context.workspace_id,
            object_type=payload.object_type,
            object_id=payload.object_id,
            action=payload.action,
            new_status=payload.new_status,
            actor_user_id=context.user_id,
            actor_role=context.role,
            reason=payload.reason,
            requested_changes=payload.requested_changes,
            metadata=payload.metadata,
        )
    except InvalidApprovalTransitionError as exc:
        raise APIError(
            409,
            "INVALID_APPROVAL_TRANSITION",
            "The approval state changed or this action is not valid for the current state.",
            details={"object_type": exc.object_type, "previous_status": exc.previous_status, "new_status": exc.new_status},
        ) from exc
    if result is None:
        raise APIError(404, "APPROVAL_OBJECT_NOT_FOUND", "The approval object was not found in this workspace.")
    event = ApprovalAuditEvent.model_validate(result["event"])
    decision = ApprovalDecision(
        object_id=payload.object_id,
        object_type=payload.object_type,
        previous_status=event.previous_status,
        new_status=event.new_status,
        action=event.action,
        reviewer_id=context.user_id,
        reviewer_role=context.role,
        reason=event.reason,
        requested_changes=event.requested_changes,
        timestamp=event.timestamp,
        metadata=event.metadata,
    )
    return ApprovalResult(decision=decision, audit_event=event, record=result["record"])


@router.get("/queue", response_model=ApprovalQueueResponse)
async def approval_queue(
    brand_id: str | None = None,
    status: ApprovalStatus | None = None,
    object_type: ApprovalObjectType | None = None,
    platform: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalQueueResponse:
    if brand_id and brand_id != context.brand_id:
        raise APIError(403, "BRAND_ACCESS_DENIED", "The selected brand does not belong to this workspace.")
    rows, total = await repository.list_approval_queue(
        workspace_id=context.workspace_id,
        brand_id=brand_id,
        status=status.value if status else None,
        object_type=object_type.value if object_type else None,
        platform=platform,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    items = [_queue_item(row["object_type"], row["payload"]) for row in rows]
    return ApprovalQueueResponse(items=items, count=total, limit=limit, offset=offset)


@router.get("/detail/{object_type}/{object_id}", response_model=ApprovalDetail)
async def approval_detail(
    object_type: ApprovalObjectType,
    object_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalDetail:
    result = await repository.get_approval_detail(context.workspace_id, object_type, object_id)
    if result is None:
        raise APIError(404, "APPROVAL_OBJECT_NOT_FOUND", "The approval object was not found in this workspace.")
    row, event_rows = result
    events = [ApprovalAuditEvent.model_validate(event) for event in event_rows]
    return _detail(object_type, row, events)


@router.get("/audit/{object_type}/{object_id}", response_model=list[ApprovalAuditEvent])
async def approval_audit(
    object_type: ApprovalObjectType,
    object_id: str,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> list[ApprovalAuditEvent]:
    result = await repository.get_approval_detail(context.workspace_id, object_type, object_id)
    if result is None:
        raise APIError(404, "APPROVAL_OBJECT_NOT_FOUND", "The approval object was not found in this workspace.")
    return [ApprovalAuditEvent.model_validate(event) for event in result[1]]


@router.post("/decision", response_model=ApprovalResult)
async def approval_decision(
    payload: ApprovalDecisionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    return await _apply(payload, repository, context)


def _decision(payload: ApprovalActionRequest, action: ApprovalAction, status: ApprovalStatus) -> ApprovalDecisionRequest:
    return ApprovalDecisionRequest(**payload.model_dump(), action=action, new_status=status)


@router.post("/submit", response_model=ApprovalResult)
async def submit(
    payload: ApprovalActionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    return await _apply(_decision(payload, ApprovalAction.SUBMIT, ApprovalStatus.IN_REVIEW), repository, context)


@router.post("/approve", response_model=ApprovalResult)
async def approve(
    payload: ApprovalActionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    return await _apply(_decision(payload, ApprovalAction.APPROVE, ApprovalStatus.APPROVED), repository, context)


@router.post("/reject", response_model=ApprovalResult)
async def reject(
    payload: ApprovalActionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    return await _apply(_decision(payload, ApprovalAction.REJECT, ApprovalStatus.REJECTED), repository, context)


@router.post("/request-changes", response_model=ApprovalResult)
async def request_changes(
    payload: ApprovalActionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    if not payload.reason.strip() or not payload.requested_changes:
        raise APIError(422, "REQUEST_CHANGES_REASON_REQUIRED", "A reason and at least one requested change are required.")
    return await _apply(
        _decision(payload, ApprovalAction.REQUEST_CHANGES, ApprovalStatus.CHANGES_REQUESTED),
        repository,
        context,
    )


@router.post("/archive", response_model=ApprovalResult)
async def archive(
    payload: ApprovalActionRequest,
    repository: ProductRepository = Depends(get_product_repository),
    context: WorkspaceContext = Depends(get_workspace_context),
) -> ApprovalResult:
    return await _apply(_decision(payload, ApprovalAction.ARCHIVE, ApprovalStatus.ARCHIVED), repository, context)
