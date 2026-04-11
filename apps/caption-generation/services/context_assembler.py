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
            target_platform=platform,
            tone_fingerprint=payload.tone_fingerprint,
            visual_profile=payload.visual_profile,
            hashtags=payload.hashtags,
            audience_profile=payload.audience_profile,
            time_windows=payload.ranked_windows,
        )
