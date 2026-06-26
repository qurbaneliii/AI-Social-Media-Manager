from __future__ import annotations


class ApprovalError(Exception):
    """Base approval lifecycle error."""


class DraftNotFoundError(ApprovalError):
    def __init__(self, object_type: str, object_id: str) -> None:
        super().__init__(f"{object_type} not found: {object_id}")
        self.object_type = object_type
        self.object_id = object_id


class InvalidApprovalTransitionError(ApprovalError):
    def __init__(self, object_type: str, previous_status: str, new_status: str) -> None:
        super().__init__(f"Invalid {object_type} transition: {previous_status} -> {new_status}")
        self.object_type = object_type
        self.previous_status = previous_status
        self.new_status = new_status
