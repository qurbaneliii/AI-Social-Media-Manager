from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


def test_legacy_caption_route_is_explicit_demo_mode() -> None:
    from main import app

    client = TestClient(app)
    response = client.post(
        "/internal/captions/generate",
        json={
            "tenant_id": "tenant-1",
            "company_id": "company-1",
            "post_id": "post-1",
            "post_intent": "educate",
            "core_message": "Approval keeps generated posts truthful.",
            "target_platforms": ["linkedin"],
            "tone_fingerprint": {"formality": 0.8},
            "visual_profile": {"palette": ["#0f766e"]},
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert response.headers["x-aria-deprecated-route"] == "legacy-caption-generator"
    assert response.headers["x-aria-demo-mode"] == "true"
    assert len(payload["variants"]) == 3
    assert payload["variants"][0]["caption_text"].startswith("Approval keeps generated posts truthful.")


def test_legacy_adapter_rejects_configured_provider_keys() -> None:
    asyncio.run(_run_legacy_adapter_configured_key_check())


async def _run_legacy_adapter_configured_key_check() -> None:
    from main import LiteLLMAdapter, Message

    adapter = LiteLLMAdapter({"openai": "configured-key"})

    with pytest.raises(RuntimeError, match="demo-only"):
        await adapter.chat("openai", "gpt-4o-mini", [Message(role="user", content="hello")])
