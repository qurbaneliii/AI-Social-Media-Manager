# FILE: packages/prompt-templates/constants.py
from __future__ import annotations

PLATFORM_CHAR_LIMITS: dict[str, int] = {
    "instagram": 2200,
    "linkedin": 3000,
    "facebook": 63206,
    "x": 280,
    "tiktok": 2200,
    "pinterest": 500,
}

HASHTAG_BROAD_THRESHOLD: int = 500_000
HASHTAG_NICHE_LOWER: int = 50_000
HASHTAG_NICHE_UPPER: int = 499_999
HASHTAG_MICRO_UPPER: int = 49_999

HASHTAG_BROAD_QUOTA: int = 3
HASHTAG_NICHE_QUOTA: int = 5
HASHTAG_MICRO_QUOTA: int = 5
HASHTAG_MAX_LENGTH_CHARS: int = 40

HASHTAG_RELEVANCE_WEIGHT: float = 0.35
HASHTAG_ENGAGEMENT_WEIGHT: float = 0.35
HASHTAG_RECENCY_WEIGHT: float = 0.20
HASHTAG_BRAND_FIT_WEIGHT: float = 0.10

CAPTION_ENGAGEMENT_WEIGHT: float = 0.30
CAPTION_TONE_MATCH_WEIGHT: float = 0.25
CAPTION_CTA_PRESENCE_WEIGHT: float = 0.15
CAPTION_KEYWORD_INCLUSION_WEIGHT: float = 0.15
CAPTION_COMPLIANCE_WEIGHT: float = 0.15

CAPTION_VARIANTS_REQUIRED: int = 3
CAPTION_COMPLIANCE_THRESHOLD: float = 0.90
CAPTION_TEMPERATURE: float = 0.75
CAPTION_FALLBACK_TOKEN_REDUCTION: float = 0.40

SEO_META_TITLE_MAX: int = 60
SEO_META_DESCRIPTION_MAX: int = 160
SEO_ALT_TEXT_MAX: int = 220
SEO_AUTO_CORRECT_MARGIN: int = 10

SEO_PRIMARY_KW_DENSITY_MIN: float = 0.015
SEO_PRIMARY_KW_DENSITY_MAX: float = 0.025
SEO_SECONDARY_KW_DENSITY_MIN: float = 0.005
SEO_SECONDARY_KW_DENSITY_MAX: float = 0.015

FLESCH_B2B_MIN: int = 45
FLESCH_B2C_MIN: int = 55

TONE_SCORE_MIN: int = 0
TONE_SCORE_MAX: int = 100
TONE_CONFIDENCE_MIN: float = 0.50
TONE_STYLE_RULES_MIN: int = 5
TONE_EMOJI_DENSITY_MIN: float = 0.0
TONE_EMOJI_DENSITY_MAX: float = 1.0

AUDIENCE_CONFIDENCE_APPROVAL_THRESHOLD: float = 0.55
AUDIENCE_AGE_RANGE_MIN: int = 13
AUDIENCE_AGE_RANGE_MAX: int = 99
AUDIENCE_GENDER_SPLIT_TOLERANCE: float = 0.05

TOKEN_BUDGET_CAPTION: int = 6000
TOKEN_BUDGET_HASHTAG: int = 2000
TOKEN_BUDGET_AUDIENCE: int = 3000
TOKEN_BUDGET_SEO: int = 2000
TOKEN_BUDGET_TONE_CALIBRATION: int = 8000

PROVIDER_FALLBACK_CHAIN: list[str] = ["deepseek", "openai", "anthropic", "mistral"]

PRIMARY_LLM_MODEL: str = "deepseek-chat"

PLATFORM_INDEXING_RULES: dict[str, str] = {
    "instagram": "Hashtags are primary discovery mechanism. Alt text indexed by accessibility crawlers.",
    "linkedin": "First 150 chars indexed for feed preview. Keywords in opening sentence prioritized.",
    "facebook": "Open Graph meta_title and meta_description used for link previews. Alt text for image search.",
    "x": "First 100 chars indexed. Hashtags boost discoverability.",
    "tiktok": "Caption keywords and hashtags drive FYP placement.",
    "pinterest": "First 50 chars of description are highest-weight. Alt text critical for visual search.",
}
