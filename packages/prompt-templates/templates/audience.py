# FILE: packages/prompt-templates/templates/audience.py
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from ..base import ChatMessages, ParsedResponse, inject_variables
from ..constants import (
    AUDIENCE_AGE_RANGE_MAX,
    AUDIENCE_AGE_RANGE_MIN,
    AUDIENCE_CONFIDENCE_APPROVAL_THRESHOLD,
    AUDIENCE_GENDER_SPLIT_TOLERANCE,
)
from ..context_models.audience_context import AudienceContext
from ..repair import attempt_json_repair

SYSTEM_PROMPT = """You are ARIA's audience targeting engine.
Return strict JSON only.
Infer platform-specific audience targeting attributes with measurable confidence.
"""

USER_PROMPT_TEMPLATE = """Generate an audience targeting profile.

Platforms: {{PLATFORMS}}
Company Profile JSON:
{{COMPANY_PROFILE_JSON}}
Post Intent: {{POST_INTENT}}
Content Topic: {{CONTENT_TOPIC}}
Value Proposition: {{VALUE_PROP}}
Top Segments JSON:
{{TOP_SEGMENTS}}
Weak Segments: {{WEAK_SEGMENTS}}
Historical Notes: {{HISTORICAL_NOTES}}

Return JSON schema:
{
  "primary_demographic": {
    "age_range": "25-44",
    "gender_split": {"female": 0.5, "male": 0.5}
  },
  "psychographic_profile": {},
  "platform_segments": {
    "facebook_custom_audience": {},
    "linkedin_audience_attributes": {},
    "x_interest_clusters": {},
    "tiktok_interest_categories": {}
  },
  "natural_language_summary": "...",
  "confidence": 0.0
}
"""


class AudienceRawResponse(BaseModel):
    """
    Direct parse target for LLM audience response.
    Maps exactly to Section 4.3 OUTPUT SCHEMA.
    """

    primary_demographic: dict
    psychographic_profile: dict
    platform_segments: dict
    natural_language_summary: str
    confidence: float = Field(ge=0.0, le=1.0)


def build_audience_targeting_prompt(context: AudienceContext) -> ChatMessages:
    """
    Build audience targeting prompt with safe variable injection.
    """
    variables = {
        "PLATFORMS": ", ".join(platform.value for platform in context.platforms),
        "COMPANY_PROFILE_JSON": context.company_profile_json,
        "POST_INTENT": context.post_intent.value,
        "CONTENT_TOPIC": context.content_topic,
        "VALUE_PROP": context.value_prop,
        "TOP_SEGMENTS": json.dumps([item.model_dump(mode="json") for item in context.top_segments], indent=2),
        "WEAK_SEGMENTS": ", ".join(context.weak_segments) or "None identified",
        "HISTORICAL_NOTES": context.historical_notes or "None available",
    }
    user_prompt = inject_variables(USER_PROMPT_TEMPLATE, variables)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_audience_targeting_response(
    raw: str,
    context: AudienceContext,
) -> ParsedResponse[AudienceRawResponse]:
    """
    Parse and validate audience response details.
    """
    repaired = attempt_json_repair(raw)
    if repaired is None:
        raise ValueError("Unrecoverable JSON parse failure")

    parsed = AudienceRawResponse.model_validate_json(repaired)

    gender_split = parsed.primary_demographic.get("gender_split")
    if not isinstance(gender_split, dict) or not gender_split:
        raise ValueError("primary_demographic.gender_split must be a non-empty object")

    gender_sum = sum(float(value) for value in gender_split.values())
    if abs(gender_sum - 1.0) > AUDIENCE_GENDER_SPLIT_TOLERANCE:
        raise ValueError(f"gender_split sum must be 1.0 ± {AUDIENCE_GENDER_SPLIT_TOLERANCE}, got {gender_sum}")

    age_range = parsed.primary_demographic.get("age_range")
    if not isinstance(age_range, str) or re.fullmatch(r"^\d{2}-\d{2}$", age_range) is None:
        raise ValueError("age_range must match ^\\d{2}-\\d{2}$")

    lower_str, upper_str = age_range.split("-")
    lower = int(lower_str)
    upper = int(upper_str)
    if lower >= upper or lower < AUDIENCE_AGE_RANGE_MIN or upper > AUDIENCE_AGE_RANGE_MAX:
        raise ValueError(
            f"age_range bounds invalid: {lower}-{upper}; required {AUDIENCE_AGE_RANGE_MIN} <= lower < upper <= {AUDIENCE_AGE_RANGE_MAX}"
        )

    required_keys = {
        "facebook_custom_audience",
        "linkedin_audience_attributes",
        "x_interest_clusters",
        "tiktok_interest_categories",
    }
    missing_keys = sorted(required_keys - set(parsed.platform_segments.keys()))
    if missing_keys:
        raise ValueError(f"Missing required platform_segments keys: {missing_keys}")

    metadata: dict[str, object] = {}
    if parsed.confidence < AUDIENCE_CONFIDENCE_APPROVAL_THRESHOLD:
        metadata["requires_approval"] = True

    return ParsedResponse(
        data=parsed,
        was_repaired=repaired != raw,
        repair_attempts=1 if repaired != raw else 0,
        raw_response=raw,
        metadata=metadata,
    )
