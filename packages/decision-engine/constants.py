# FILE: packages/decision-engine/constants.py
from __future__ import annotations

# -- 5.1 Hashtag Selection -------------------------------------------------
HASHTAG_LLM_CANDIDATE_COUNT: int = 40
HASHTAG_VECTOR_CANDIDATE_COUNT: int = 100
HASHTAG_RELEVANCE_THRESHOLD: float = 0.62
HASHTAG_SCORE_THRESHOLD: float = 0.55
HASHTAG_RECENCY_DECAY_DAYS: int = 30
HASHTAG_RECENCY_THRESHOLD: float = 0.20
HASHTAG_UNDERFILL_SCORE_PENALTY: float = 0.03

HASHTAG_BROAD_VOLUME_MIN: int = 500_000
HASHTAG_NICHE_VOLUME_MIN: int = 50_000
HASHTAG_NICHE_VOLUME_MAX: int = 499_999
HASHTAG_MICRO_VOLUME_MAX: int = 49_999

HASHTAG_BROAD_RELEVANCE_MIN: float = 0.65
HASHTAG_NICHE_RELEVANCE_MIN: float = 0.68
HASHTAG_MICRO_RELEVANCE_MIN: float = 0.72

HASHTAG_QUOTA_BROAD: int = 3
HASHTAG_QUOTA_NICHE: int = 5
HASHTAG_QUOTA_MICRO: int = 5

HASHTAG_PLATFORM_CAPS: dict[str, int] = {
    "x": 3,
    "linkedin": 5,
    "facebook": 5,
    "instagram": 20,
    "tiktok": 8,
    "pinterest": 10,
}

HASHTAG_WEIGHT_RELEVANCE: float = 0.35
HASHTAG_WEIGHT_PERFORMANCE: float = 0.35
HASHTAG_WEIGHT_RECENCY: float = 0.20
HASHTAG_WEIGHT_BRAND_FIT: float = 0.10

# -- 5.2 Audience Resolution ----------------------------------------------
AUDIENCE_LLM_CONFIDENCE_HIGH_THRESHOLD: float = 0.75
AUDIENCE_HIGH_CONF_WEIGHT_COMPANY: float = 0.55
AUDIENCE_HIGH_CONF_WEIGHT_LLM: float = 0.45
AUDIENCE_LOW_CONF_WEIGHT_COMPANY: float = 0.80
AUDIENCE_LOW_CONF_WEIGHT_LLM: float = 0.20
AUDIENCE_LOCATION_OVERLAP_MIN: float = 0.40
AUDIENCE_AGE_OVERLAP_MIN_PERCENT: int = 30
AUDIENCE_CONFLICT_CODE_OVERRIDE: str = "AUDIENCE_OVERRIDE"
AUDIENCE_BASELINE_CONFIDENCE: float = 0.85
AUDIENCE_APPROVAL_MIN_CONFIDENCE: float = 0.55

# -- 5.3 Posting Time Selection -------------------------------------------
POSTING_QUEUE_UTILIZATION_MAX: float = 0.85
POSTING_MIN_CONFIDENCE: float = 0.60
POSTING_DEADLINE_SAFETY_BUFFER_MINUTES: int = 30
POSTING_OVERRIDE_WINDOW_DURATION_MINUTES: int = 15

POSTING_COOLDOWN_HOURS: dict[str, int] = {
    "instagram": 6,
    "linkedin": 12,
    "facebook": 6,
    "x": 1,
    "tiktok": 8,
    "pinterest": 4,
}

POSTING_REGION_UTC_OFFSETS: dict[str, int] = {
    "US_EST": -5,
    "US_PST": -8,
    "UK_GMT": 0,
    "EU_CET": 1,
    "APAC_SGT": 8,
}

POSTING_REGION_HOURLY_ENGAGEMENT_PRIORS: dict[str, dict[int, float]] = {
    "US_EST": {8: 0.45, 12: 0.75, 18: 0.90, 21: 0.70},
    "US_PST": {8: 0.40, 12: 0.70, 18: 0.88, 21: 0.68},
    "UK_GMT": {8: 0.50, 12: 0.78, 18: 0.86, 21: 0.64},
    "EU_CET": {8: 0.52, 12: 0.80, 18: 0.84, 21: 0.62},
    "APAC_SGT": {8: 0.48, 12: 0.74, 18: 0.89, 21: 0.66},
}

POSTING_GLOBAL_SCORE_BASE_MULTIPLIER: float = 0.85
POSTING_GLOBAL_SCORE_SCALE: float = 0.15

# -- 5.4 Tone Adaptation ---------------------------------------------------
TONE_SCORE_MIN: int = 0
TONE_SCORE_MAX: int = 100

INTENT_DELTAS: dict[str, dict[str, int]] = {
    "announce": {
        "formality": +8,
        "humor": -3,
        "assertiveness": +4,
        "clarity": +6,
    },
    "educate": {
        "formality": +12,
        "humor": -5,
        "assertiveness": +3,
        "clarity": +10,
    },
    "promote": {
        "formality": +5,
        "humor": +2,
        "assertiveness": +15,
        "urgency": +10,
    },
    "engage": {
        "formality": -8,
        "humor": +12,
        "assertiveness": +2,
        "warmth": +10,
    },
    "inspire": {
        "formality": +2,
        "humor": +4,
        "assertiveness": -4,
        "optimism": +15,
        "storytelling": +12,
    },
    "crisis_response": {
        "formality": +20,
        "humor": -30,
        "assertiveness": +10,
        "empathy": +18,
    },
}

PLATFORM_TONE_MODIFIERS: dict[str, dict[str, int | float]] = {
    "linkedin": {"formality": +8},
    "tiktok": {"humor": +10},
    "x": {"sentence_length_factor": -0.20},
}

TONE_MIN_AVG_SENTENCE_LENGTH: float = 1.0

CRISIS_REQUIRED_EMPATHY: bool = True
CRISIS_FORBIDDEN_CTA_TOKENS: list[str] = [
    "buy now",
    "shop now",
    "limited offer",
    "discount",
    "sale",
    "purchase",
    "order now",
    "promo",
]

# -- 5.5 Platform Routing --------------------------------------------------
ROUTING_STYLE_DISTANCE_THRESHOLD: float = 0.25
ROUTING_ASPECT_MISMATCH_THRESHOLD: float = 0.15
ROUTING_OVERFLOW_SOFT_MAX: float = 0.20

PLATFORM_PREFERRED_ASPECT_RATIOS: dict[str, list[tuple[int, int]]] = {
    "instagram": [(1, 1), (4, 5)],
    "tiktok": [(9, 16)],
    "pinterest": [(2, 3)],
    "linkedin": [(1, 1), (1200, 627)],
    "facebook": [(1, 1), (1200, 630)],
    "x": [(16, 9), (1, 1)],
}

PLATFORM_HASHTAG_STRATEGY: dict[str, dict] = {
    "x": {"max": 3, "preferred_tiers": ["niche", "micro"]},
    "linkedin": {"max": 5, "preferred_tiers": ["niche"]},
    "instagram": {"max": 13, "preferred_tiers": ["broad", "niche", "micro"]},
    "facebook": {"max": 5, "preferred_tiers": ["broad", "niche"]},
    "tiktok": {"max": 8, "preferred_tiers": ["niche", "micro"]},
    "pinterest": {"max": 10, "preferred_tiers": ["broad", "niche"]},
}
