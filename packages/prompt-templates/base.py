# FILE: packages/prompt-templates/base.py
from __future__ import annotations

import re
from typing import Any, Generic, Literal, TypedDict, TypeVar

import tiktoken
from pydantic import BaseModel, Field


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


ChatMessages = list[ChatMessage]


class PromptVariableError(ValueError):
    """Raised when a {{PLACEHOLDER}} is not resolved after injection."""

    unresolved: list[str]

    def __init__(self, unresolved: list[str]) -> None:
        self.unresolved = unresolved
        super().__init__(f"Unresolved prompt variables: {', '.join(unresolved)}")


class PromptValidationError(ValueError):
    """Raised when pre-send prompt validation fails."""

    checks_failed: list[str]

    def __init__(self, checks_failed: list[str]) -> None:
        self.checks_failed = checks_failed
        super().__init__("Prompt validation failed: " + " | ".join(checks_failed))


class RepairResult(BaseModel):
    repaired_json: str | None
    was_repaired: bool
    attempts: int = Field(ge=0)


T = TypeVar("T")


class ParsedResponse(BaseModel, Generic[T]):
    """Wrapper for parsed LLM response with repair metadata."""

    data: T
    was_repaired: bool
    repair_attempts: int = Field(ge=0)
    raw_response: str
    metadata: dict[str, Any] = Field(default_factory=dict)


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}")
_ENCODING = tiktoken.get_encoding("cl100k_base")


def inject_variables(template: str, variables: dict[str, str]) -> str:
    """
    Replace all {{VARIABLE_NAME}} placeholders in template with values
    from the variables dict.

    After substitution, scan for any remaining {{...}} patterns.
    If any unresolved placeholders found, raise PromptVariableError
    with the list of unresolved names.

    Variable names in the template are always UPPER_SNAKE_CASE between {{ }}.
    """

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        return match.group(0)

    rendered = _PLACEHOLDER_RE.sub(replacer, template)
    unresolved = sorted(set(_PLACEHOLDER_RE.findall(rendered)))
    if unresolved:
        raise PromptVariableError(unresolved)
    return rendered


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base encoding."""
    return len(_ENCODING.encode(text))


def estimate_prompt_tokens(messages: ChatMessages) -> int:
    """Sum token counts across all message content fields."""
    return sum(count_tokens(message["content"]) for message in messages)
