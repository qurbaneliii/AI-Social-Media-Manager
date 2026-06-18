from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .brand import BrandProfile
from .content import PlatformContext


class VisualConceptRequest(BaseModel):
    brand_profile: BrandProfile
    platform_context: PlatformContext
    topic: str
    content_pillar: str
    campaign_objective: str
    creative_constraints: list[str] = Field(default_factory=list)


class VisualConceptPackage(BaseModel):
    visual_brief: str
    carousel_concepts: list[dict[str, Any]] = Field(default_factory=list)
    short_form_video_concepts: list[dict[str, Any]] = Field(default_factory=list)
    image_generation_prompts: list[str] = Field(default_factory=list)
    design_direction: dict[str, Any] = Field(default_factory=dict)
    mood: list[str] = Field(default_factory=list)
    scene: str
    layout: str
    creative_constraints: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)

