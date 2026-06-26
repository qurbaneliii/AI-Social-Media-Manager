from __future__ import annotations

from typing import Any

from ai.persistence import AIPersistenceRepository

from .errors import DraftNotFoundError
from .schemas import ApprovalAuditEvent, ApprovalDecision, ApprovalObjectType, ApprovalResult, ApprovalStatus
from .transitions import validate_transition


class ApprovalService:
    def __init__(self, repository: AIPersistenceRepository) -> None:
        self.repository = repository

    async def apply_decision(self, decision: ApprovalDecision) -> ApprovalResult:
        record = await self._get_record(decision.object_type, decision.object_id)
        if record is None:
            raise DraftNotFoundError(decision.object_type.value, decision.object_id)

        previous_status = self._extract_status(record, decision.object_type)
        resolved_decision = decision.model_copy(update={"previous_status": previous_status})
        validate_transition(decision.object_type, previous_status, decision.new_status)

        updated = await self._update_status(resolved_decision)
        audit_event = await self.repository.store_approval_audit_event(resolved_decision)
        return ApprovalResult(
            decision=resolved_decision,
            audit_event=ApprovalAuditEvent.model_validate(audit_event),
            record=updated,
        )

    async def list_audit_events(self, object_type: ApprovalObjectType, object_id: str) -> list[ApprovalAuditEvent]:
        events = await self.repository.list_approval_audit_events(object_type.value, object_id)
        return [ApprovalAuditEvent.model_validate(event) for event in events]

    async def _get_record(self, object_type: ApprovalObjectType, object_id: str) -> dict[str, Any] | None:
        if object_type == ApprovalObjectType.CONTENT_DRAFT:
            return await self.repository.get_content_draft_by_id(object_id)
        if object_type == ApprovalObjectType.CALENDAR_DRAFT:
            return await self.repository.get_calendar_draft_item_by_id(object_id)
        if object_type == ApprovalObjectType.COMMUNITY_REPLY:
            return await self.repository.get_community_reply_draft_by_id(object_id)
        if object_type == ApprovalObjectType.REPORT_DRAFT:
            return await self.repository.get_report_draft_by_id(object_id)
        return None

    async def _update_status(self, decision: ApprovalDecision) -> dict[str, Any]:
        if decision.object_type == ApprovalObjectType.CONTENT_DRAFT:
            return await self.repository.update_content_draft_approval_status(decision.object_id, decision.new_status.value)
        if decision.object_type == ApprovalObjectType.CALENDAR_DRAFT:
            return await self.repository.update_calendar_draft_approval_status(decision.object_id, decision.new_status.value)
        if decision.object_type == ApprovalObjectType.COMMUNITY_REPLY:
            return await self.repository.update_community_reply_approval_status(decision.object_id, decision.new_status.value)
        if decision.object_type == ApprovalObjectType.REPORT_DRAFT:
            return await self.repository.update_report_draft_approval_status(decision.object_id, decision.new_status.value)
        raise DraftNotFoundError(decision.object_type.value, decision.object_id)

    def _extract_status(self, record: dict[str, Any], object_type: ApprovalObjectType) -> ApprovalStatus:
        status = record.get("approval_status") or record.get("draft_status")
        if status is None:
            raise DraftNotFoundError(object_type.value, str(record.get("id", "")))
        return ApprovalStatus(status)
