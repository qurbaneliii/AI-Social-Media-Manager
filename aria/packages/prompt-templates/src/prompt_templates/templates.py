from __future__ import annotations

import json
from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


ChatMessages = list[ChatMessage]


class CaptionContext(BaseModel):
    post_intent: str
    core_message: str
    platform: str
    tone_fingerprint: dict
    visual_profile: dict
    target_audience: dict


class HashtagContext(BaseModel):
    platform: str
    keywords: list[str]
    prior_hashtag_performance: dict[str, float] = Field(default_factory=dict)


class AudienceContext(BaseModel):
    company_summary: str
    segments: list[str]
    platforms: list[str]


class SEOContext(BaseModel):
    topic: str
    keywords: list[str]
    intent: str


class ToneContext(BaseModel):
    base_fingerprint: dict
    post_intent: str


class CaptionParseResult(BaseModel):
    variants: list[dict]


class HashtagParseResult(BaseModel):
    hashtags: list[str]


class AudienceParseResult(BaseModel):
    profile: dict


class SEOParseResult(BaseModel):
    metadata: dict


class ToneParseResult(BaseModel):
    calibrated_tone: dict


def build_caption_generation_prompt(context: CaptionContext) -> ChatMessages:
    system_prompt = "You are ARIA caption generation engine. Return strict JSON."
    user_prompt = (
        "Generate at least 3 caption variants. "
        f"intent={context.post_intent}; platform={context.platform}; core_message={context.core_message}; "
        f"tone={json.dumps(context.tone_fingerprint)}; visual={json.dumps(context.visual_profile)}; "
        f"audience={json.dumps(context.target_audience)}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_caption_generation_response(raw: str) -> CaptionParseResult:
    return CaptionParseResult.model_validate(json.loads(raw))


def build_hashtag_generation_prompt(context: HashtagContext) -> ChatMessages:
    system_prompt = "You are ARIA hashtag generator. Return strict JSON with ranked hashtags."
    user_prompt = (
        f"platform={context.platform}; keywords={json.dumps(context.keywords)}; "
        f"priors={json.dumps(context.prior_hashtag_performance)}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_hashtag_generation_response(raw: str) -> HashtagParseResult:
    return HashtagParseResult.model_validate(json.loads(raw))


def build_audience_targeting_prompt(context: AudienceContext) -> ChatMessages:
    system_prompt = "You are ARIA audience targeting engine. Return strict JSON audience profile."
    user_prompt = (
        f"company_summary={context.company_summary}; segments={json.dumps(context.segments)}; "
        f"platforms={json.dumps(context.platforms)}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_audience_targeting_response(raw: str) -> AudienceParseResult:
    return AudienceParseResult.model_validate(json.loads(raw))


def build_seo_optimization_prompt(context: SEOContext) -> ChatMessages:
    system_prompt = "You are ARIA SEO optimization engine. Return strict JSON metadata object."
    user_prompt = f"topic={context.topic}; intent={context.intent}; keywords={json.dumps(context.keywords)}"
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_seo_optimization_response(raw: str) -> SEOParseResult:
    return SEOParseResult.model_validate(json.loads(raw))


def build_tone_calibration_prompt(context: ToneContext) -> ChatMessages:
    system_prompt = "You are ARIA tone calibration engine. Return strict JSON calibrated_tone object."
    user_prompt = f"base_tone={json.dumps(context.base_fingerprint)}; post_intent={context.post_intent}"
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_tone_calibration_response(raw: str) -> ToneParseResult:
    return ToneParseResult.model_validate(json.loads(raw))
