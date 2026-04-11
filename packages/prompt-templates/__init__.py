# FILE: packages/prompt-templates/__init__.py
from packages.prompt_templates.base import (
    ChatMessage,
    ChatMessages,
    ParsedResponse,
    PromptValidationError,
    PromptVariableError,
    count_tokens,
    inject_variables,
)
from packages.prompt_templates.templates.audience import (
    build_audience_targeting_prompt,
    parse_audience_targeting_response,
)
from packages.prompt_templates.templates.caption import (
    build_caption_generation_prompt,
    parse_caption_generation_response,
)
from packages.prompt_templates.templates.hashtag import (
    build_hashtag_generation_prompt,
    parse_hashtag_generation_response,
)
from packages.prompt_templates.templates.seo import (
    build_seo_optimization_prompt,
    parse_seo_optimization_response,
)
from packages.prompt_templates.templates.tone_calibration import (
    build_tone_calibration_prompt,
    parse_tone_calibration_response,
)

__all__ = [
    "ChatMessage",
    "ChatMessages",
    "ParsedResponse",
    "PromptVariableError",
    "PromptValidationError",
    "inject_variables",
    "count_tokens",
    "build_caption_generation_prompt",
    "parse_caption_generation_response",
    "build_hashtag_generation_prompt",
    "parse_hashtag_generation_response",
    "build_audience_targeting_prompt",
    "parse_audience_targeting_response",
    "build_seo_optimization_prompt",
    "parse_seo_optimization_response",
    "build_tone_calibration_prompt",
    "parse_tone_calibration_response",
]
