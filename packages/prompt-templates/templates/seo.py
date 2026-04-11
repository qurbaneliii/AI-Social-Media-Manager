# FILE: packages/prompt-templates/templates/seo.py
from __future__ import annotations

import json

from pydantic import BaseModel, Field

from ..base import ChatMessages, ParsedResponse, inject_variables
from ..constants import (
    PLATFORM_INDEXING_RULES,
    SEO_ALT_TEXT_MAX,
    SEO_AUTO_CORRECT_MARGIN,
    SEO_META_DESCRIPTION_MAX,
    SEO_META_TITLE_MAX,
)
from ..context_models.seo_context import SEOContext
from ..repair import attempt_json_repair

SYSTEM_PROMPT = """You are ARIA's SEO optimization engine.
Return strict JSON only.
Optimize metadata for discoverability while respecting strict character limits.
"""

USER_PROMPT_TEMPLATE = """Optimize SEO metadata for this post.

Post Caption:
{{POST_CAPTION}}
Image Description:
{{IMAGE_DESCRIPTION}}
Industry Vertical: {{INDUSTRY_VERTICAL}}
Target Keywords: {{TARGET_KEYWORDS}}
Platform Indexing Rules:
{{PLATFORM_INDEXING_RULES}}

Return JSON schema:
{
  "meta_title": "...",
  "meta_description": "...",
  "alt_text": "...",
  "keywords": ["..."],
  "keyword_density_targets": {}
}
"""


class SEORawResponse(BaseModel):
    meta_title: str = Field(max_length=SEO_META_TITLE_MAX)
    meta_description: str = Field(max_length=SEO_META_DESCRIPTION_MAX)
    alt_text: str = Field(max_length=SEO_ALT_TEXT_MAX)
    keywords: list[str] = Field(min_length=1, max_length=15)
    keyword_density_targets: dict


def _truncate_to_word_boundary(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    head = value[:max_len]
    boundary = head.rfind(" ")
    if boundary <= 0:
        return head.rstrip()
    return head[:boundary].rstrip()


def _enforce_length(value: str, max_len: int, label: str) -> tuple[str, bool]:
    over = len(value) - max_len
    if over <= 0:
        return value, False
    if over <= SEO_AUTO_CORRECT_MARGIN:
        return _truncate_to_word_boundary(value, max_len), True
    raise ValueError(f"{label} exceeds max length {max_len} by {over} characters")


def build_seo_optimization_prompt(context: SEOContext) -> ChatMessages:
    """
    Build SEO optimization prompt.
    """
    variables = {
        "POST_CAPTION": context.post_caption,
        "IMAGE_DESCRIPTION": context.image_description or "No image provided",
        "INDUSTRY_VERTICAL": context.industry_vertical,
        "TARGET_KEYWORDS": ", ".join(context.target_keywords),
        "PLATFORM_INDEXING_RULES": PLATFORM_INDEXING_RULES[context.platform.value],
    }
    user_prompt = inject_variables(USER_PROMPT_TEMPLATE, variables)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_seo_optimization_response(
    raw: str,
    context: SEOContext,
) -> ParsedResponse[SEORawResponse]:
    """
    Parse SEO response with deterministic length enforcement.
    """
    repaired = attempt_json_repair(raw)
    if repaired is None:
        raise ValueError("Unrecoverable JSON parse failure")

    payload = json.loads(repaired)
    if not isinstance(payload, dict):
        raise ValueError("SEO response must be a JSON object")

    was_repaired = repaired != raw
    attempts = 1 if repaired != raw else 0

    title, title_fixed = _enforce_length(str(payload.get("meta_title", "")), SEO_META_TITLE_MAX, "meta_title")
    desc, desc_fixed = _enforce_length(
        str(payload.get("meta_description", "")),
        SEO_META_DESCRIPTION_MAX,
        "meta_description",
    )
    alt, alt_fixed = _enforce_length(str(payload.get("alt_text", "")), SEO_ALT_TEXT_MAX, "alt_text")
    if title_fixed or desc_fixed or alt_fixed:
        was_repaired = True

    payload["meta_title"] = title
    payload["meta_description"] = desc
    payload["alt_text"] = alt

    parsed = SEORawResponse.model_validate(payload)

    banned = [term.strip().casefold() for term in context.banned_vocabulary if term.strip()]
    fields_to_scan = [parsed.meta_title, parsed.meta_description, parsed.alt_text, " ".join(parsed.keywords)]
    for term in banned:
        for field in fields_to_scan:
            if term in field.casefold():
                raise ValueError(f"SEO output contains banned vocabulary term '{term}'")

    return ParsedResponse(
        data=parsed,
        was_repaired=was_repaired,
        repair_attempts=attempts,
        raw_response=raw,
    )
