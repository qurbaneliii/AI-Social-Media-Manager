# FILE: packages/prompt-templates/tests/test_repair.py
from __future__ import annotations

from packages.prompt_templates.repair import (
    attempt_json_repair,
    build_repair_system_prompt,
    build_repair_user_prompt,
)


def test_attempt_json_repair_direct_valid() -> None:
    raw = '{"ok": true}'
    assert attempt_json_repair(raw) == raw


def test_attempt_json_repair_strip_whitespace() -> None:
    raw = '  {"ok": true}  '
    assert attempt_json_repair(raw) == raw


def test_attempt_json_repair_extract_object() -> None:
    raw = 'prefix text {"a": 1} trailing text'
    assert attempt_json_repair(raw) == '{"a": 1}'


def test_attempt_json_repair_extract_array() -> None:
    raw = 'noise [1, 2, 3] more noise'
    assert attempt_json_repair(raw) == '[1, 2, 3]'


def test_attempt_json_repair_strip_code_fence() -> None:
    raw = '```json\n{"k":"v"}\n```'
    assert attempt_json_repair(raw) == '{"k":"v"}'


def test_attempt_json_repair_failure_none() -> None:
    assert attempt_json_repair('not-json') is None


def test_repair_prompt_builders() -> None:
    system = build_repair_system_prompt()
    user = build_repair_user_prompt("orig", "bad", "schema")
    assert "CRITICAL" in system
    assert "orig" in user and "bad" in user and "schema" in user
