from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMMetadata(BaseModel):
    provider: str = "openai"
    model: str
    mock_mode: bool
    token_usage: dict[str, int] = Field(default_factory=dict)
    raw_response_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

