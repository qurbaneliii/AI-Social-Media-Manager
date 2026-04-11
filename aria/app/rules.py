# filename: app/rules.py
# purpose: Deterministic rule-based guards for validation, safety, scheduling, signature checks, idempotency, and budgets.
# dependencies: datetime, hashlib, hmac, re, typing

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime
from typing import Any


class BudgetExceededError(Exception):
    """Raised when token or call budgets are exceeded."""


def validate_payload(data: dict[str, Any], schema: dict[str, Any]) -> None:
    """
    Validate nested payload using a simple deterministic schema descriptor.

    Schema format example:
    {
      "field": {"type": str, "required": True},
      "age": {"type": int, "min": 0, "max": 120},
      "nested": {"type": dict, "schema": {...}},
      "tags": {"type": list, "item_type": str, "min_length": 1}
    }
    """

    def _validate(value: Any, descriptor: dict[str, Any], path: str) -> None:
        required = descriptor.get("required", True)
        if value is None:
            if required:
                raise ValueError(f"{path}: missing required value")
            return

        expected_type = descriptor.get("type")
        if expected_type is not None and not isinstance(value, expected_type):
            raise ValueError(
                f"{path}: expected {expected_type.__name__}, got {type(value).__name__}"
            )

        if isinstance(value, (int, float)):
            if "min" in descriptor and value < descriptor["min"]:
                raise ValueError(f"{path}: value {value} below min {descriptor['min']}")
            if "max" in descriptor and value > descriptor["max"]:
                raise ValueError(f"{path}: value {value} above max {descriptor['max']}")

        if isinstance(value, str):
            if "min_length" in descriptor and len(value) < descriptor["min_length"]:
                raise ValueError(
                    f"{path}: length {len(value)} below min_length {descriptor['min_length']}"
                )
            if "max_length" in descriptor and len(value) > descriptor["max_length"]:
                raise ValueError(
                    f"{path}: length {len(value)} above max_length {descriptor['max_length']}"
                )

        if isinstance(value, list):
            if "min_length" in descriptor and len(value) < descriptor["min_length"]:
                raise ValueError(
                    f"{path}: list length {len(value)} below min_length {descriptor['min_length']}"
                )
            if "max_length" in descriptor and len(value) > descriptor["max_length"]:
                raise ValueError(
                    f"{path}: list length {len(value)} above max_length {descriptor['max_length']}"
                )
            item_type = descriptor.get("item_type")
            for idx, item in enumerate(value):
                item_path = f"{path}[{idx}]"
                if item_type is not None and not isinstance(item, item_type):
                    raise ValueError(
                        f"{item_path}: expected {item_type.__name__}, got {type(item).__name__}"
                    )

        if isinstance(value, dict) and "schema" in descriptor:
            nested_schema = descriptor["schema"]
            for key, nested_descriptor in nested_schema.items():
                nested_value = value.get(key)
                _validate(nested_value, nested_descriptor, f"{path}.{key}")

    for field_name, field_descriptor in schema.items():
        _validate(data.get(field_name), field_descriptor, field_name)


def filter_banned_vocabulary(text: str, banned: list[str]) -> str:
    """Remove banned terms from text using case-insensitive full-token replacement."""
    result = text
    for term in banned:
        cleaned = term.strip()
        if not cleaned:
            continue
        pattern = re.compile(re.escape(cleaned), flags=re.IGNORECASE)
        result = pattern.sub("", result)
    return re.sub(r"\s{2,}", " ", result).strip()


def enforce_hashtag_cap(hashtags: list[str], platform: str) -> list[str]:
    """Apply deterministic hashtag caps by platform."""
    caps = {
        "instagram": 30,
        "linkedin": 5,
        "x": 5,
        "tiktok": 10,
    }
    cap = caps.get(platform.lower(), 10)
    return hashtags[:cap]


def enforce_char_limit(text: str, platform: str) -> str:
    """Apply platform-specific character limits with last-full-word truncation."""
    limits = {
        "instagram": 2200,
        "linkedin": 3000,
        "x": 280,
        "tiktok": 2200,
    }
    limit = limits.get(platform.lower(), 2200)
    if len(text) <= limit:
        return text

    head = text[:limit]
    cut = head.rfind(" ")
    if cut <= 0:
        return head
    return head[:cut]


def check_scheduling_collision(
    proposed: datetime,
    existing: list[datetime],
    cooldown_seconds: int,
) -> bool:
    """Return True when proposed schedule is safe relative to existing times."""
    for scheduled in existing:
        if abs((proposed - scheduled).total_seconds()) < cooldown_seconds:
            return False
    return True


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate HMAC-SHA256 signature for a webhook payload."""
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    provided = signature.strip()
    if provided.startswith("sha256="):
        provided = provided.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


def is_duplicate(key: str, seen: set[str]) -> bool:
    """Return True if key has already been observed."""
    if key in seen:
        return True
    seen.add(key)
    return False


def check_cost_guardrail(
    token_count: int,
    call_count: int,
    token_budget: int,
    call_budget: int,
) -> None:
    """Raise BudgetExceededError if token or call budgets are exceeded."""
    if token_count > token_budget:
        raise BudgetExceededError(
            f"Token budget exceeded: {token_count} > {token_budget}"
        )
    if call_count > call_budget:
        raise BudgetExceededError(
            f"Call budget exceeded: {call_count} > {call_budget}"
        )
