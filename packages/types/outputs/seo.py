# FILE: packages/types/outputs/seo.py
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..enums import FontStyle, LayoutType


class SeoMetadata(BaseModel):
    """Implements Section 3.2.5 Output E SEO metadata model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    meta_title: Annotated[str, Field(min_length=1, max_length=60)]
    meta_description: Annotated[str, Field(min_length=1, max_length=160)]
    alt_text: Annotated[str, Field(min_length=1, max_length=220)]


class VisualProfile(BaseModel):
    """Implements Section 3.2.5 Output E visual profile model for SEO context."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    layout_type: LayoutType
    font_style: FontStyle
    brand_consistency_score: float = Field(ge=0.0, le=1.0)


class SeoOutput(BaseModel):
    """Implements Section 3.2.5 Output E SEO output response."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_id: UUID
    seo_metadata: SeoMetadata
    visual_profile: VisualProfile | None = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    generated_at: datetime
