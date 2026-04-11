# FILE: packages/types/outputs/post_generation.py
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .audience import AudienceOutput
from .caption import CaptionGenerationOutput
from .hashtag import HashtagOutput
from .quality import QualityOutput
from .schedule import ScheduleOutput
from .seo import SeoOutput


class PostGenerationOutput(BaseModel):
    """Implements Section 3.2.7 Output G final assembled post generation package."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    post_id: UUID
    company_id: UUID
    status: Literal["generating", "generated", "failed"]
    caption: CaptionGenerationOutput
    hashtags: HashtagOutput
    audience: AudienceOutput
    schedule: ScheduleOutput
    seo: SeoOutput
    quality: QualityOutput
    degraded_mode: bool = False
    generated_at: datetime
