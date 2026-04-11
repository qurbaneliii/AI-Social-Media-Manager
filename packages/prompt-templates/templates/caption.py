# FILE: packages/prompt-templates/templates/caption.py
from __future__ import annotations

import json
from collections import Counter

from pydantic import BaseModel, ValidationInfo, field_validator

from ..base import ChatMessages, ParsedResponse, inject_variables
from ..constants import CAPTION_VARIANTS_REQUIRED, PLATFORM_CHAR_LIMITS
from ..context_models.caption_context import CaptionContext
from ..repair import attempt_json_repair
from packages.types.enums import CTAType, Platform

SYSTEM_PROMPT = """You are ARIA's caption generation engine.
You must return strict JSON only.
Do not include markdown or commentary.
Generate compliant, platform-aware variants that preserve brand voice and intent.
"""

USER_PROMPT_TEMPLATE = """Generate caption variants using the context below.

Company Name: {{COMPANY_NAME}}
Company Positioning: {{COMPANY_POSITIONING}}
Post Intent: {{POST_INTENT}}
Core Message: {{CORE_MESSAGE}}
Campaign Tag: {{CAMPAIGN_TAG}}
CTA Requirements: {{CTA_REQUIREMENTS}}
Visual Context Summary: {{VISUAL_CONTEXT_SUMMARY}}
Image OCR Text: {{IMAGE_OCR_TEXT}}
Tone Fingerprint JSON:
{{TONE_FINGERPRINT_JSON}}
Audience Profile JSON:
{{AUDIENCE_PROFILE_JSON}}
Visual Tone Scores JSON:
{{VISUAL_TONE_SCORES_JSON}}
Approved Vocabulary: {{APPROVED_VOCABULARY_LIST}}
Banned Vocabulary: {{BANNED_VOCABULARY_LIST}}
SEO Keywords: {{SEO_KEYWORDS}}
Secondary Keywords: {{SECONDARY_KEYWORDS}}
Target Platforms: {{TARGET_PLATFORMS}}
Platform Constraints JSON:
{{PLATFORM_CONSTRAINTS_JSON}}

Output schema:
{
  "variants": [
    {
      "platform": "instagram|linkedin|facebook|x|tiktok|pinterest",
      "variant_id": "v1|v2|v3",
      "text": "...",
      "char_count": 123,
      "contains_cta": true,
      "included_keywords": ["..."]
    }
  ]
}

Return only JSON.
"""


class CaptionVariantRaw(BaseModel):
    """Parsed from LLM response before scoring."""

    platform: Platform
    variant_id: str
    text: str
    char_count: int
    contains_cta: bool
    included_keywords: list[str]
    cta_type: CTAType | None = None


class CaptionRawResponse(BaseModel):
    variants: list[CaptionVariantRaw]

    @field_validator("variants")
    @classmethod
    def validate_variant_distribution(
        cls,
        value: list[CaptionVariantRaw],
        info: ValidationInfo,
    ) -> list[CaptionVariantRaw]:
        context = info.context or {}
        platforms = context.get("platforms", [])
        if not platforms:
            return value

        expected_total = CAPTION_VARIANTS_REQUIRED * len(platforms)
        if len(value) != expected_total:
            raise ValueError(
                f"Expected {expected_total} variants for {len(platforms)} platforms, got {len(value)}"
            )

        counts = Counter(item.platform.value for item in value)
        bad_counts = {
            platform: count
            for platform, count in counts.items()
            if platform in platforms and count != CAPTION_VARIANTS_REQUIRED
        }
        missing = [platform for platform in platforms if platform not in counts]
        if bad_counts or missing:
            raise ValueError(
                "Each platform must have exactly "
                f"{CAPTION_VARIANTS_REQUIRED} variants. bad_counts={bad_counts}, missing={missing}"
            )

        return value


def build_caption_generation_prompt(context: CaptionContext) -> ChatMessages:
    """
    Assemble the full messages array for caption generation.

    Steps:
    1. Serialize context fields to their prompt string representations.
    2. Build variables dict mapping every {{VARIABLE_NAME}} to its value.
    3. Call inject_variables(USER_PROMPT_TEMPLATE, variables).
    4. Return [system_message, user_message] as ChatMessages.
    """
    variables = {
        "COMPANY_NAME": context.company_name,
        "COMPANY_POSITIONING": context.company_positioning,
        "POST_INTENT": context.post_intent.value,
        "CORE_MESSAGE": context.core_message,
        "CAMPAIGN_TAG": context.campaign_tag or "None",
        "CTA_REQUIREMENTS": ", ".join(context.cta_requirements),
        "VISUAL_CONTEXT_SUMMARY": context.visual_context_summary or "None",
        "IMAGE_OCR_TEXT": context.image_ocr_text or "None",
        "TONE_FINGERPRINT_JSON": json.dumps(context.tone_fingerprint, indent=2),
        "AUDIENCE_PROFILE_JSON": json.dumps(context.audience_profile, indent=2),
        "VISUAL_TONE_SCORES_JSON": json.dumps(context.visual_tone_scores, indent=2),
        "APPROVED_VOCABULARY_LIST": ", ".join(context.approved_vocabulary_list) or "None",
        "BANNED_VOCABULARY_LIST": ", ".join(context.banned_vocabulary_list) or "None",
        "SEO_KEYWORDS": ", ".join(context.seo_keywords),
        "SECONDARY_KEYWORDS": ", ".join(context.secondary_keywords) or "None",
        "TARGET_PLATFORMS": ", ".join(platform.value for platform in context.target_platforms),
        "PLATFORM_CONSTRAINTS_JSON": json.dumps(
            [item.model_dump(mode="json") for item in context.platform_constraints],
            indent=2,
        ),
    }

    user_prompt = inject_variables(USER_PROMPT_TEMPLATE, variables)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_caption_generation_response(
    raw: str,
    context: CaptionContext,
) -> ParsedResponse[CaptionRawResponse]:
    """
    Parse and validate LLM caption response.
    """
    repaired = attempt_json_repair(raw)
    if repaired is None:
        raise ValueError("Unrecoverable JSON parse failure")

    parsed = CaptionRawResponse.model_validate_json(
        repaired,
        context={"platforms": [platform.value for platform in context.target_platforms]},
    )

    was_repaired = repaired != raw
    repair_attempts = 1 if repaired != raw else 0

    corrected_variants: list[CaptionVariantRaw] = []
    banned_terms = [term.casefold() for term in context.banned_vocabulary_list if term.strip()]

    for variant in parsed.variants:
        actual_char_count = len(variant.text)
        if variant.char_count != actual_char_count:
            variant = variant.model_copy(update={"char_count": actual_char_count})
            was_repaired = True

        text_norm = variant.text.casefold()
        for banned_term in banned_terms:
            if banned_term in text_norm:
                raise ValueError(
                    f"Variant {variant.variant_id} contains banned term '{banned_term}'"
                )

        max_chars = PLATFORM_CHAR_LIMITS[variant.platform.value]
        if variant.char_count > max_chars:
            overage = variant.char_count - max_chars
            raise ValueError(
                f"Variant {variant.variant_id} exceeds {variant.platform.value} limit by {overage} chars"
            )

        corrected_variants.append(variant)

    result = parsed.model_copy(update={"variants": corrected_variants})
    return ParsedResponse(
        data=result,
        was_repaired=was_repaired,
        repair_attempts=repair_attempts,
        raw_response=raw,
    )
