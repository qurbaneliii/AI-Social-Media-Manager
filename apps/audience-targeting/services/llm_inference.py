# FILE: apps/audience-targeting/services/llm_inference.py
from __future__ import annotations

import httpx


class LlmInference:
    def __init__(self, llm_client: httpx.AsyncClient, llm_proxy_url: str) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url

    async def process(self, campaign_context: str, segments: list[str]) -> dict:
        """Infer psychographic audience profile via structured LLM JSON output."""
        response = await self.llm_client.post(
            f"{self.llm_proxy_url}/v1/llm/proxy/chat",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Return JSON with age_range(min,max), psychographics object, confidence."},
                    {"role": "user", "content": f"context={campaign_context}; segments={segments}"},
                ],
                "response_format": "json",
                "temperature": 0.2,
                "max_tokens": 800,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        output = response.json().get("output", {})
        if not isinstance(output, dict):
            output = {}
        return {
            "age_range": output.get("age_range", {"min_age": 25, "max_age": 45}),
            "psychographics": output.get("psychographics", {"value_seeking": 0.7}),
            "confidence": float(output.get("confidence", 0.6)),
        }
