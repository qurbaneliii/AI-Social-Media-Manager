# FILE: apps/caption-generation/services/provider_router.py
from __future__ import annotations

import json

import httpx
from prompt_templates import build_caption_generation_prompt


class ProviderRouter:
    def __init__(self, llm_client: httpx.AsyncClient, llm_proxy_url: str) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url
        self.providers = ["deepseek", "openai", "anthropic", "mistral"]

    async def _send(self, provider: str, messages: list[dict], max_tokens: int) -> dict:
        response = await self.llm_client.post(
            f"{self.llm_proxy_url}/v1/llm/proxy/chat",
            json={
                "provider": provider,
                "model": "default",
                "messages": messages,
                "response_format": "json",
                "temperature": 0.75,
                "max_tokens": max_tokens,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        out = response.json().get("output", {})
        if isinstance(out, str):
            return json.loads(out)
        if isinstance(out, dict):
            return out
        raise ValueError("Invalid provider output format")

    async def process(self, context) -> list[dict]:
        """Generate three variants with provider-chain fallback, timeout retry, and JSON strict retry."""
        base_messages = build_caption_generation_prompt(context)
        variants: list[dict] = []

        for _ in range(3):
            produced = None
            for provider in self.providers:
                try:
                    produced = await self._send(provider, base_messages, 800)
                    break
                except httpx.TimeoutException:
                    produced = await self._send(provider, base_messages, int(800 * 0.6))
                    break
                except json.JSONDecodeError:
                    strict_messages = [{"role": "system", "content": "Respond with strict JSON only."}] + base_messages
                    produced = await self._send(provider, strict_messages, 800)
                    break
                except Exception:  # noqa: BLE001
                    continue
            if produced is None:
                raise RuntimeError("All providers failed")
            variants.append(produced)

        return variants
