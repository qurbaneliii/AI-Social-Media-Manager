# FILE: packages/types/inputs/post_request.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import Platform, PostIntent, UrgencyLevel


class AttachedMedia(BaseModel):
    """Implements Section 3.1.2 Input B nested attached media model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    media_id: UUID
    mime_type: Annotated[str, Field(min_length=1, max_length=50)]

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, value: str) -> str:
        """Restricts attached media MIME type to allowed image/video set."""
        allowed = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"}
        if value not in allowed:
            raise ValueError(f"mime_type must be one of {sorted(allowed)}")
        return value


class PostGenerationRequest(BaseModel):
    """Implements Section 3.1.2 Input B PostGenerationRequest."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    post_intent: PostIntent
    core_message: Annotated[str, Field(min_length=20, max_length=500)]
    target_platforms: Annotated[list[Platform], Field(min_length=1, max_length=6)]
    campaign_tag: Annotated[str, Field(max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")] | None = None
    attached_media: AttachedMedia | None = None
    manual_keywords: Annotated[list[Annotated[str, Field(min_length=1, max_length=80)]], Field(max_length=20)] = Field(default_factory=list)
    urgency_level: UrgencyLevel
    requested_publish_at: datetime | None = None

    @field_validator("target_platforms")
    @classmethod
    def validate_unique_platforms(cls, value: list[Platform]) -> list[Platform]:
        """Ensures no duplicate platforms in target_platforms."""
        seen: set[str] = set()
        duplicates: list[str] = []
        for platform in value:
            platform_value = str(platform)
            if platform_value in seen:
                duplicates.append(platform_value)
            seen.add(platform_value)
        if duplicates:
            raise ValueError(f"Duplicate platforms are not allowed: {sorted(set(duplicates))}")
        return value

    @model_validator(mode="after")
    def validate_urgency_publish_time(self) -> "PostGenerationRequest":
        """Applies urgency scheduling rules for requested_publish_at."""
        now_plus_5 = datetime.now(UTC) + timedelta(minutes=5)
        if self.urgency_level == UrgencyLevel.scheduled:
            if self.requested_publish_at is None:
                raise ValueError("requested_publish_at is required when urgency_level is scheduled")
            publish_at = self.requested_publish_at
            if publish_at.tzinfo is None:
                publish_at = publish_at.replace(tzinfo=UTC)
            if publish_at <= now_plus_5:
                raise ValueError("requested_publish_at must be at least 5 minutes in the future")
        if self.urgency_level == UrgencyLevel.immediate and self.requested_publish_at is not None:
            raise ValueError("requested_publish_at must be None when urgency_level is immediate")
        return self
