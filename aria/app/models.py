# filename: app/models.py
# purpose: Pydantic v2 API contracts for request validation and response serialization.
# dependencies: typing, pydantic

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


GenerationModule = Literal[
    "generate_caption",
    "generate_hashtags",
    "generate_audience",
    "generate_seo_metadata",
    "calibrate_tone",
]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=128)
    module: GenerationModule
    payload: dict[str, Any]
    max_tokens: int = Field(default=512, ge=32, le=4096)


class GenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cached: bool
    task_id: str | None = None
    result: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class TaskStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class RouterStatusItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["open", "closed", "half-open"]
    failure_count: int
    last_failure_timestamp: float | None


class RouterStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: dict[str, RouterStatusItem]


class QueuedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queued: bool


class PostListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, Any]]
    limit: int
    offset: int


class PostDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: dict[str, Any] | None


EmbeddingTable = Literal[
    "brand_voice_embeddings",
    "hashtag_embeddings",
    "post_archive_embeddings",
    "audience_profile_embeddings",
]


class EmbeddingSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    table: EmbeddingTable
    query_embedding: list[float] = Field(min_length=1)
    k: int = Field(default=10, ge=1, le=200)
    filters: dict[str, Any] = Field(default_factory=dict)


class EmbeddingSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, Any]]


class AuditListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, Any]]
    limit: int
    offset: int
