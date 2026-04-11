# FILE: packages/prompt-templates/templates/tone_calibration.py
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from ..base import ChatMessages, ParsedResponse, inject_variables
from ..constants import TONE_CONFIDENCE_MIN, TONE_STYLE_RULES_MIN
from ..context_models.tone_context import ToneContext
from ..repair import attempt_json_repair
from packages.types.enums import CTAType, ReadingLevel

SYSTEM_PROMPT = """You are ARIA's tone calibration engine.
Return strict JSON only.
Derive a stable tone fingerprint from historical examples and brand constraints.
"""

USER_PROMPT_TEMPLATE = """Calibrate brand tone using this context.

Company Name: {{COMPANY_NAME}}
Tone Descriptors: {{TONE_DESCRIPTORS}}
Brand Positioning:
{{BRAND_POSITIONING}}

Sample Posts:
{{SAMPLE_POSTS_TEXT_BLOCK}}

Competitor Tone Analysis:
{{COMPETITOR_TONE_ANALYSIS}}

Approved Vocabulary: {{APPROVED_VOCAB}}
Banned Vocabulary: {{BANNED_VOCAB}}

Return JSON schema:
{
  "tone_fingerprint": {
    "formality_score": 0,
    "humor_score": 0,
    "assertiveness_score": 0,
    "optimism_score": 0,
    "emoji_density_target": 0.0,
    "avg_sentence_length_target": 12.0,
    "reading_level_target": "grade_9_to_12",
    "preferred_cta_types": ["learn_more"],
    "style_rules": ["..."],
    "lexical_signature": {
      "top_keywords": [{"term": "...", "weight": 0.1}],
      "forbidden_terms": ["..."]
    },
    "intent_modifiers": {
            "announce": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            },
            "educate": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            },
            "promote": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            },
            "engage": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            },
            "inspire": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            },
            "crisis_response": {
                "delta": {
                    "formality": 0,
                    "humor": 0,
                    "assertiveness": 0
                }
            }
    }
  },
  "confidence": 0.0
}
"""


class IntentModifierDelta(BaseModel):
    formality: int = Field(ge=-20, le=20)
    humor: int = Field(ge=-20, le=20)
    assertiveness: int = Field(ge=-20, le=20)


class IntentModifier(BaseModel):
    delta: IntentModifierDelta


class LexicalSignature(BaseModel):
    top_keywords: list[dict]
    forbidden_terms: list[str]


class ToneFingerprintRaw(BaseModel):
    formality_score: int = Field(ge=0, le=100)
    humor_score: int = Field(ge=0, le=100)
    assertiveness_score: int = Field(ge=0, le=100)
    optimism_score: int = Field(ge=0, le=100)
    emoji_density_target: float = Field(ge=0.0, le=1.0)
    avg_sentence_length_target: float = Field(ge=1.0)
    reading_level_target: ReadingLevel
    preferred_cta_types: list[CTAType] = Field(min_length=1)
    style_rules: list[str] = Field(min_length=TONE_STYLE_RULES_MIN)
    lexical_signature: LexicalSignature
    intent_modifiers: dict[str, IntentModifier]

    @field_validator("intent_modifiers")
    @classmethod
    def validate_intent_modifiers(cls, value: dict[str, IntentModifier]) -> dict[str, IntentModifier]:
        required = {
            "announce",
            "educate",
            "promote",
            "engage",
            "inspire",
            "crisis_response",
        }
        missing = sorted(required - set(value.keys()))
        if missing:
            raise ValueError(f"Missing intent modifier keys: {missing}")
        extra = sorted(set(value.keys()) - required)
        if extra:
            raise ValueError(f"Unexpected intent modifier keys: {extra}")
        return value


class ToneCalibrationRawResponse(BaseModel):
    tone_fingerprint: ToneFingerprintRaw
    confidence: float = Field(ge=0.0, le=1.0)


def build_tone_calibration_prompt(context: ToneContext) -> ChatMessages:
    """
    Build tone calibration prompt.
    """
    sample_blocks: list[str] = []
    for sample in context.sample_posts:
        engagement = sample.engagement_rate if sample.engagement_rate is not None else "unknown"
        sample_blocks.append(
            f"[Platform: {sample.platform.value}]\n"
            f"{sample.text}\n"
            f"Engagement: {engagement}\n"
            "---"
        )

    variables = {
        "COMPANY_NAME": context.company_name,
        "TONE_DESCRIPTORS": ", ".join(context.tone_descriptors),
        "BRAND_POSITIONING": context.brand_positioning,
        "SAMPLE_POSTS_TEXT_BLOCK": "\n".join(sample_blocks),
        "COMPETITOR_TONE_ANALYSIS": context.competitor_tone_analysis or "Not provided",
        "APPROVED_VOCAB": ", ".join(context.approved_vocabulary) or "None specified",
        "BANNED_VOCAB": ", ".join(context.banned_vocabulary) or "None specified",
    }
    user_prompt = inject_variables(USER_PROMPT_TEMPLATE, variables)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def parse_tone_calibration_response(
    raw: str,
    context: ToneContext,
) -> ParsedResponse[ToneCalibrationRawResponse]:
    """
    Parse tone calibration response with confidence and vocabulary safeguards.
    """
    repaired = attempt_json_repair(raw)
    if repaired is None:
        raise ValueError("Unrecoverable JSON parse failure")

    parsed = ToneCalibrationRawResponse.model_validate_json(repaired)
    if parsed.confidence < TONE_CONFIDENCE_MIN:
        raise ValueError(
            f"Confidence {parsed.confidence} below minimum {TONE_CONFIDENCE_MIN}. "
            "Provide more sample posts."
        )

    if len(parsed.tone_fingerprint.style_rules) < TONE_STYLE_RULES_MIN:
        raise ValueError(
            f"style_rules must contain at least {TONE_STYLE_RULES_MIN} entries"
        )

    was_repaired = repaired != raw
    attempts = 1 if repaired != raw else 0

    forbidden = {term.casefold(): term for term in parsed.tone_fingerprint.lexical_signature.forbidden_terms}
    missing = [term for term in context.banned_vocabulary if term.casefold() not in forbidden]

    if missing:
        updated_forbidden_terms = parsed.tone_fingerprint.lexical_signature.forbidden_terms + missing
        lexical_signature = parsed.tone_fingerprint.lexical_signature.model_copy(
            update={"forbidden_terms": updated_forbidden_terms}
        )
        fingerprint = parsed.tone_fingerprint.model_copy(update={"lexical_signature": lexical_signature})
        parsed = parsed.model_copy(update={"tone_fingerprint": fingerprint})
        was_repaired = True

    return ParsedResponse(
        data=parsed,
        was_repaired=was_repaired,
        repair_attempts=attempts,
        raw_response=raw,
    )
