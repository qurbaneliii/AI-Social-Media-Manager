from __future__ import annotations

from .errors import InvalidApprovalTransitionError
from .schemas import ApprovalObjectType, ApprovalStatus


TRANSITIONS: dict[ApprovalObjectType, dict[ApprovalStatus, set[ApprovalStatus]]] = {
    ApprovalObjectType.CONTENT_DRAFT: {
        ApprovalStatus.DRAFT: {
            ApprovalStatus.IN_REVIEW,
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.IN_REVIEW: {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.CHANGES_REQUESTED: {ApprovalStatus.DRAFT},
        ApprovalStatus.APPROVED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.REJECTED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.ARCHIVED: set(),
    },
    ApprovalObjectType.CALENDAR_DRAFT: {
        ApprovalStatus.DRAFT: {ApprovalStatus.IN_REVIEW},
        ApprovalStatus.IN_REVIEW: {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.APPROVED: {ApprovalStatus.READY_FOR_SCHEDULING},
        ApprovalStatus.READY_FOR_SCHEDULING: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.REJECTED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.CHANGES_REQUESTED: {ApprovalStatus.DRAFT},
        ApprovalStatus.ARCHIVED: set(),
    },
    ApprovalObjectType.COMMUNITY_REPLY: {
        ApprovalStatus.DRAFT: {ApprovalStatus.IN_REVIEW},
        ApprovalStatus.IN_REVIEW: {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.ESCALATED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.CHANGES_REQUESTED: {ApprovalStatus.DRAFT},
        ApprovalStatus.APPROVED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.ESCALATED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.REJECTED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.ARCHIVED: set(),
    },
    ApprovalObjectType.REPORT_DRAFT: {
        ApprovalStatus.DRAFT: {
            ApprovalStatus.IN_REVIEW,
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.IN_REVIEW: {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CHANGES_REQUESTED,
        },
        ApprovalStatus.CHANGES_REQUESTED: {ApprovalStatus.DRAFT},
        ApprovalStatus.APPROVED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.REJECTED: {ApprovalStatus.ARCHIVED},
        ApprovalStatus.ARCHIVED: set(),
    },
}


FORBIDDEN_RUNTIME_STATES = {"published", "scheduled", "sent"}


def validate_transition(
    object_type: ApprovalObjectType,
    previous_status: ApprovalStatus,
    new_status: ApprovalStatus,
) -> None:
    if previous_status.value in FORBIDDEN_RUNTIME_STATES or new_status.value in FORBIDDEN_RUNTIME_STATES:
        raise InvalidApprovalTransitionError(object_type.value, previous_status.value, new_status.value)

    allowed = TRANSITIONS.get(object_type, {}).get(previous_status, set())
    if new_status not in allowed:
        raise InvalidApprovalTransitionError(object_type.value, previous_status.value, new_status.value)
