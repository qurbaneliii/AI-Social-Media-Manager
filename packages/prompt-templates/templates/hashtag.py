# FILE: packages/prompt-templates/templates/hashtag.py
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from ..base import ChatMessages, ParsedResponse, inject_variables
from ..constants import (
    HASHTAG_BROAD_QUOTA,
    HASHTAG_MAX_LENGTH_CHARS,
    HASHTAG_MICRO_QUOTA,
    HASHTAG_NICHE_QUOTA,
)
from ..context_models.hashtag_context import HashtagContext
from ..repair import attempt_json_repair

SYSTEM_PROMPT = """You are ARIA's hashtag generation engine.
Return strict JSON only with tiered hashtags.
Never include markdown or explanatory text.
"""

USER_PROMPT_TEMPLATE = """Generate hashtags for the following context.

Platform: {{PLATFORM}}
Post Topic: {{POST_TOPIC}}
Industry Vertical: {{INDUSTRY_VERTICAL}}
Audience Summary: {{AUDIENCE_SUMMARY}}
Brand Positioning: {{BRAND_POSITIONING}}
Trending Context:
{{TRENDING_CONTEXT}}
Historical Tags: {{HISTORICAL_TAGS}}
Banned Tags: {{BANNED_TAGS}}

Return JSON with exact schema:
{
  "broad": [{"tag": "#example", "reason": "..."}],
  "niche": [{"tag": "#example", "reason": "..."}],
  "micro": [{"tag": "#example", "reason": "..."}]
}

Quotas: broad=3, niche=5, micro=5.
"""


class HashtagEntryRaw(BaseModel):
    tag: str
    reason: str

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, value: str) -> str:
        if not value.startswith("#"):
            raise ValueError("hashtag must start with #")
        if len(value) > HASHTAG_MAX_LENGTH_CHARS:
            raise ValueError(
                f"hashtag exceeds max length {HASHTAG_MAX_LENGTH_CHARS}: {value}"
            )
        if " " in value:
            raise ValueError("hashtag cannot contain spaces")
        if value[1:] != value[1:].lower():
            raise ValueError("hashtag must be lowercase after #")
        return value


class HashtagRawResponse(BaseModel):
    broad: list[HashtagEntryRaw]
    niche: list[HashtagEntryRaw]
    micro: list[HashtagEntryRaw]

    @model_validator(mode="after")
    def validate_quotas_and_uniqueness(self) -> "HashtagRawResponse":
        if len(self.broad) != HASHTAG_BROAD_QUOTA:
            raise ValueError(f"broad must contain exactly {HASHTAG_BROAD_QUOTA} items")
        if len(self.niche) != HASHTAG_NICHE_QUOTA:
            raise ValueError(f"niche must contain exactly {HASHTAG_NICHE_QUOTA} items")
        if len(self.micro) != HASHTAG_MICRO_QUOTA:
            raise ValueError(f"micro must contain exactly {HASHTAG_MICRO_QUOTA} items")

        all_tags = [item.tag for item in self.broad + self.niche + self.micro]
        if len(set(all_tags)) != len(all_tags):
            raise ValueError("no tag may appear in more than one tier")
        return self


def build_hashtag_generation_prompt(context: HashtagContext) -> ChatMessages:
    """
    Build messages for hashtag generation.
    """
    variables = {
        "PLATFORM": context.platform.value,
        "POST_TOPIC": context.post_topic,
        "INDUSTRY_VERTICAL": context.industry_vertical,
        "AUDIENCE_SUMMARY": context.audience_summary,
        "BRAND_POSITIONING": context.brand_positioning,
        "TRENDING_CONTEXT": "\n".join(context.trending_context) or "None available",
        "HISTORICAL_TAGS": ", ".join(context.historical_tags) or "None available",
        "BANNED_TAGS": ", ".join(context.banned_tags) or "None",
    }
    user_prompt = inject_variables(USER_PROMPT_TEMPLATE, variables)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_hashtag_generation_response(
    raw: str,
    context: HashtagContext,
) -> ParsedResponse[HashtagRawResponse]:
    """
    Parse hashtag response and remove banned tags while preserving partial output.
    """
    repaired = attempt_json_repair(raw)
    if repaired is None:
        raise ValueError("Unrecoverable JSON parse failure")

    parsed = HashtagRawResponse.model_validate_json(repaired)
    was_repaired = repaired != raw
    repair_attempts = 1 if repaired != raw else 0

    banned = {tag.casefold() for tag in context.banned_tags}

    broad = [entry for entry in parsed.broad if entry.tag.casefold() not in banned]
    niche = [entry for entry in parsed.niche if entry.tag.casefold() not in banned]
    micro = [entry for entry in parsed.micro if entry.tag.casefold() not in banned]

    warnings: list[str] = []
    deficits: dict[str, int] = {}

    if len(broad) < HASHTAG_BROAD_QUOTA:
        deficits["broad"] = HASHTAG_BROAD_QUOTA - len(broad)
    if len(niche) < HASHTAG_NICHE_QUOTA:
        deficits["niche"] = HASHTAG_NICHE_QUOTA - len(niche)
    if len(micro) < HASHTAG_MICRO_QUOTA:
        deficits["micro"] = HASHTAG_MICRO_QUOTA - len(micro)

    if deficits:
        was_repaired = True
        warnings.append(
            f"Banned tag removal created tier deficits: {deficits}. Returning partial result."
        )

    if (broad, niche, micro) != (parsed.broad, parsed.niche, parsed.micro):
        was_repaired = True

    result = HashtagRawResponse.model_construct(broad=broad, niche=niche, micro=micro)
    return ParsedResponse(
        data=result,
        was_repaired=was_repaired,
        repair_attempts=repair_attempts,
        raw_response=raw,
        metadata={"warnings": warnings, "deficits": deficits},
    )
