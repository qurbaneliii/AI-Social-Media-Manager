# FILE: packages/prompt-templates/repair.py
from __future__ import annotations

import json
import re


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def attempt_json_repair(raw: str) -> str | None:
    """
    Attempt to extract valid JSON from a potentially malformed response.

    Strategy (in order, stop on first success):
    1. Try json.loads(raw) directly.
    2. Strip leading/trailing whitespace and try again.
    3. Extract content between first { and last } and try.
    4. Extract content between first [ and last ] and try.
    5. Strip markdown code fences (```json ... ```) and try.
    6. Return None if all strategies fail.

    Return the raw extracted JSON string (not parsed dict) on success,
    or None on failure.
    """

    def is_valid(candidate: str) -> bool:
        try:
            json.loads(candidate)
            return True
        except json.JSONDecodeError:
            return False

    if is_valid(raw):
        return raw

    stripped = raw.strip()
    if is_valid(stripped):
        return stripped

    first_obj = stripped.find("{")
    last_obj = stripped.rfind("}")
    if first_obj != -1 and last_obj != -1 and first_obj < last_obj:
        candidate = stripped[first_obj : last_obj + 1]
        if is_valid(candidate):
            return candidate

    first_arr = stripped.find("[")
    last_arr = stripped.rfind("]")
    if first_arr != -1 and last_arr != -1 and first_arr < last_arr:
        candidate = stripped[first_arr : last_arr + 1]
        if is_valid(candidate):
            return candidate

    unfenced = _CODE_FENCE_RE.sub("", stripped).strip()
    if is_valid(unfenced):
        return unfenced

    return None


def build_repair_system_prompt() -> str:
    """
    Return a strict system prompt override for repair calls.
    Used when initial parse fails — prepended to the original
    system prompt in the repair call.
    """
    return (
        "CRITICAL: Your previous response was not valid JSON. "
        "Return ONLY the JSON object with no other text, "
        "no markdown, no code fences, no explanation. "
        "Start your response with { and end with }."
    )


def build_repair_user_prompt(
    original_user_prompt: str,
    raw_failed_response: str,
    expected_schema: str,
) -> str:
    """
    Build the user message for a repair call.
    Includes the original prompt, the failed response,
    and the expected schema as a reminder.
    """
    return (
        "Original request:\n"
        f"{original_user_prompt}\n\n"
        "Invalid response to repair:\n"
        f"{raw_failed_response}\n\n"
        "Expected JSON schema (must match exactly):\n"
        f"{expected_schema}\n\n"
        "Return only corrected JSON."
    )
