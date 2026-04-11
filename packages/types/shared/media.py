# FILE: packages/types/shared/media.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MimeType(StrEnum):
    """Implements Section 3 shared MIME type enumeration for media references."""

    image_jpeg = "image/jpeg"
    image_png = "image/png"
    image_webp = "image/webp"
    video_mp4 = "video/mp4"
    video_quicktime = "video/quicktime"


class MediaReference(BaseModel):
    """Implements Section 3 shared media reference model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    media_id: UUID
    s3_uri: Annotated[str, Field(pattern=r"^s3://[a-z0-9.-]+/.+$")]
    mime_type: MimeType
    size_bytes: int = Field(ge=1)
    width_px: int | None = Field(default=None, ge=1)
    height_px: int | None = Field(default=None, ge=1)
    uploaded_at: datetime

    @model_validator(mode="after")
    def validate_dimensions_for_media_type(self) -> "MediaReference":
        """Enforces required image dimensions and optional video dimensions."""
        if self.mime_type.value.startswith("image/"):
            if self.width_px is None or self.height_px is None:
                raise ValueError("width_px and height_px are required for image media types")
        return self
