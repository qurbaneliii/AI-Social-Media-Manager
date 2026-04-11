# FILE: packages/prompt-templates/src/prompt_templates/caption.py
from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field


class CaptionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_intent: str
    core_message: str
    target_platform: str
    tone_fingerprint: dict = Field(default_factory=dict)
    visual_profile: dict = Field(default_factory=dict)
    hashtags: list[str] = Field(default_factory=list)
    audience_profile: dict = Field(default_factory=dict)
    time_windows: list[dict] = Field(default_factory=list)


def build_caption_generation_prompt(context: CaptionContext) -> list[dict[str, str]]:
    system_prompt = "You are ARIA caption generator. Output strict JSON with caption_text, policy_compliance_score, cta_present, keyword_inclusion."
    user_prompt = (
        f"intent={context.post_intent}; platform={context.target_platform}; message={context.core_message}; "
        f"tone={json.dumps(context.tone_fingerprint)}; visual={json.dumps(context.visual_profile)}; "
        f"hashtags={json.dumps(context.hashtags)}; audience={json.dumps(context.audience_profile)}; "
        f"time_windows={json.dumps(context.time_windows)}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
