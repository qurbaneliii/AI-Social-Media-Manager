# FILE: apps/scheduler/models/output.py
from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field

from types_shared import StrictBaseModel


class WorkflowRunOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    run_id: str
    status: str
    generated_at: datetime


class WebhookOutput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern=r"^(accepted|rejected)$")
    event_type: str
