# FILE: packages/prompt-templates/context_models/hashtag_context.py
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from packages.types.enums import Platform


class HashtagContext(BaseModel):
    company_id: UUID
    platform: Platform
    post_topic: str = Field(min_length=10, max_length=300)
    industry_vertical: str = Field(min_length=2)
    audience_summary: str = Field(min_length=10)
    brand_positioning: str = Field(min_length=10)
    trending_context: list[str] = Field(default_factory=list)
    historical_tags: list[str] = Field(default_factory=list)
    banned_tags: list[str] = Field(default_factory=list)

    @field_validator("historical_tags")
    @classmethod
    def validate_historical_tags(cls, value: list[str]) -> list[str]:
        for tag in value:
            if not tag.startswith("#"):
                raise ValueError(f"historical tag must start with #: {tag}")
            if " " in tag:
                raise ValueError(f"historical tag cannot contain spaces: {tag}")
        return value

    @field_validator("banned_tags")
    @classmethod
    def validate_banned_tags(cls, value: list[str]) -> list[str]:
        for tag in value:
            if not tag.startswith("#"):
                raise ValueError(f"banned tag must start with #: {tag}")
        return value
