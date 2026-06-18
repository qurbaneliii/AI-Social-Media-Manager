from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentExecutionResult(BaseModel):
    agent_name: str
    status: str = "completed"
    mock_mode: bool
    approval_required: bool = True
    output: dict[str, Any] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)

