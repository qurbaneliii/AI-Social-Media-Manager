# FILE: apps/caption-generation/services/context_assembler.py
from __future__ import annotations

from prompt_templates import CaptionContext

from models.input import CaptionGenerationInput


class ContextAssembler:
    def __init__(self) -> None:
        pass

    async def process(self, payload: CaptionGenerationInput, platform: str) -> CaptionContext:
        """Assemble all module outputs into a unified caption context model."""
        return CaptionContext(
            post_intent=payload.post_intent.value,
            core_message=payload.core_message,
            platform=platform,
            tone_fingerprint=payload.tone_fingerprint or {},
            visual_profile=payload.visual_profile or {},
            target_audience=payload.audience_profile or {},
        )
