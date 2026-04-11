# FILE: apps/visual-understanding/models/input.py
from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict, Field, HttpUrl

from types_shared import StrictBaseModel


class VisualUnderstandingInput(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: UUID = Field(..., description="Company identifier")
    image_url: HttpUrl | None = Field(None, description="Public image URL")
    image_base64: str | None = Field(None, min_length=16, description="Base64 image bytes")
    logo_present_expected: bool = Field(default=False)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        model = super().model_validate(obj, *args, **kwargs)
        if not model.image_url and not model.image_base64:
            raise ValueError("Either image_url or image_base64 must be provided")
        return model
