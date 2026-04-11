# FILE: packages/prompt-templates/validators.py
from __future__ import annotations

import json
from collections.abc import Iterable

import textstat

from .base import ChatMessages, PromptValidationError, estimate_prompt_tokens
from .constants import (
    FLESCH_B2B_MIN,
    FLESCH_B2C_MIN,
    TOKEN_BUDGET_AUDIENCE,
    TOKEN_BUDGET_CAPTION,
    TOKEN_BUDGET_HASHTAG,
    TOKEN_BUDGET_SEO,
    TOKEN_BUDGET_TONE_CALIBRATION,
)
from .context_models import AudienceContext, CaptionContext, HashtagContext, SEOContext, ToneContext
from packages.types.enums import MarketSegment, Platform, PostIntent


def _has_unresolved_placeholders(messages: ChatMessages) -> bool:
    return any("{{" in message["content"] or "}}" in message["content"] for message in messages)


def _raise_if_failures(failures: list[str], warnings: list[str]) -> bool:
    if failures:
        raise PromptValidationError(failures + warnings)
    return True


def _is_non_empty_text(value: str) -> bool:
    return bool(value and value.strip())


def _contains_any_term(text: str, terms: Iterable[str]) -> str | None:
    text_norm = text.casefold()
    for term in terms:
        t = term.strip()
        if t and t.casefold() in text_norm:
            return t
    return None


def validate_caption_prompt(messages: ChatMessages, context: CaptionContext) -> bool:
    checks_failed: list[str] = []
    warnings: list[str] = []

    if _has_unresolved_placeholders(messages):
        checks_failed.append("Unresolved template placeholders remain in caption prompt")
    if estimate_prompt_tokens(messages) >= TOKEN_BUDGET_CAPTION:
        checks_failed.append("Caption prompt token budget exceeded")
    if not context.banned_vocabulary_list:
        checks_failed.append("caption context banned_vocabulary_list must not be empty")
    if not context.platform_constraints:
        checks_failed.append("caption context platform_constraints must not be empty")
    if len(context.target_platforms) < 1:
        checks_failed.append("caption context target_platforms must include at least one platform")
    if len(context.seo_keywords) < 1:
        checks_failed.append("caption context seo_keywords must include at least one keyword")
    if len(context.core_message) < 20:
        checks_failed.append("caption context core_message must be at least 20 characters")

    return _raise_if_failures(checks_failed, warnings)


def validate_hashtag_prompt(messages: ChatMessages, context: HashtagContext) -> bool:
    checks_failed: list[str] = []
    warnings: list[str] = []

    if _has_unresolved_placeholders(messages):
        checks_failed.append("Unresolved template placeholders remain in hashtag prompt")
    if estimate_prompt_tokens(messages) >= TOKEN_BUDGET_HASHTAG:
        checks_failed.append("Hashtag prompt token budget exceeded")
    if not isinstance(context.platform, Platform) or context.platform.value not in {p.value for p in Platform}:
        checks_failed.append("hashtag context platform must be a valid Platform value")
    if context.banned_tags is None:
        checks_failed.append("hashtag context banned_tags must be loaded (empty list allowed)")
    if not _is_non_empty_text(context.post_topic):
        checks_failed.append("hashtag context post_topic must not be empty")
    if not _is_non_empty_text(context.industry_vertical):
        checks_failed.append("hashtag context industry_vertical must not be empty")

    return _raise_if_failures(checks_failed, warnings)


def validate_audience_prompt(messages: ChatMessages, context: AudienceContext) -> bool:
    checks_failed: list[str] = []
    warnings: list[str] = []

    if _has_unresolved_placeholders(messages):
        checks_failed.append("Unresolved template placeholders remain in audience prompt")
    if estimate_prompt_tokens(messages) >= TOKEN_BUDGET_AUDIENCE:
        checks_failed.append("Audience prompt token budget exceeded")
    if len(context.platforms) < 1:
        checks_failed.append("audience context platforms must include at least one platform")
    try:
        json.loads(context.company_profile_json)
    except json.JSONDecodeError:
        checks_failed.append("audience context company_profile_json must be valid JSON")
    if not isinstance(context.post_intent, PostIntent) or context.post_intent.value not in {p.value for p in PostIntent}:
        checks_failed.append("audience context post_intent must be a valid PostIntent")

    return _raise_if_failures(checks_failed, warnings)


def validate_seo_prompt(messages: ChatMessages, context: SEOContext) -> bool:
    checks_failed: list[str] = []
    warnings: list[str] = []

    if _has_unresolved_placeholders(messages):
        checks_failed.append("Unresolved template placeholders remain in SEO prompt")
    if estimate_prompt_tokens(messages) >= TOKEN_BUDGET_SEO:
        checks_failed.append("SEO prompt token budget exceeded")
    if not _is_non_empty_text(context.post_caption):
        checks_failed.append("seo context post_caption must not be empty")
    if len(context.target_keywords) < 1:
        checks_failed.append("seo context target_keywords must include at least one keyword")

    score = textstat.flesch_reading_ease(context.post_caption)
    threshold = FLESCH_B2B_MIN if context.market_segment == MarketSegment.B2B else FLESCH_B2C_MIN
    if score < threshold:
        warnings.append(
            f"[WARNING] Flesch score {score:.2f} below threshold {threshold} for market segment {context.market_segment.value}"
        )

    offending_term = _contains_any_term(context.post_caption, context.banned_vocabulary)
    if offending_term is not None:
        checks_failed.append(f"seo context post_caption contains banned vocabulary term '{offending_term}'")

    return _raise_if_failures(checks_failed, warnings)


def validate_tone_calibration_prompt(messages: ChatMessages, context: ToneContext) -> bool:
    checks_failed: list[str] = []
    warnings: list[str] = []

    if _has_unresolved_placeholders(messages):
        checks_failed.append("Unresolved template placeholders remain in tone calibration prompt")
    if estimate_prompt_tokens(messages) >= TOKEN_BUDGET_TONE_CALIBRATION:
        checks_failed.append("Tone calibration prompt token budget exceeded")
    if len(context.sample_posts) < 5:
        checks_failed.append("tone context requires at least 5 sample_posts")
    if len(context.tone_descriptors) < 3:
        checks_failed.append("tone context requires at least 3 tone_descriptors")
    if context.banned_vocabulary is None:
        checks_failed.append("tone context banned_vocabulary must not be None")
    if not _is_non_empty_text(context.brand_positioning):
        checks_failed.append("tone context brand_positioning must not be empty")

    return _raise_if_failures(checks_failed, warnings)
