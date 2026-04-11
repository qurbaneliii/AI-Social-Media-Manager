# FILE: apps/scheduler/models/input.py
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from types_shared import ApprovalMode, Platform, StrictBaseModel


class WorkflowRunInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_name: Literal["PostGenerationWorkflow", "PostPublishWorkflow", "PerformanceFeedbackWorkflow"]
    schedule_id: UUID
    post_id: UUID
    company_id: UUID
    platform: Platform
    approval_mode: ApprovalMode = ApprovalMode.auto
    oauth_token_expires_at: datetime | None = None


class WebhookInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    signature: str = Field(..., min_length=10)
    payload: dict = Field(default_factory=dict)
