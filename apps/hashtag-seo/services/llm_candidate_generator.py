# FILE: apps/hashtag-seo/services/llm_candidate_generator.py
from __future__ import annotations

import httpx


class LlmCandidateGenerator:
    def __init__(self, llm_client: httpx.AsyncClient, llm_proxy_url: str) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url

    async def process(self, core_text: str, keywords: list[str]) -> list[str]:
        """Generate exactly 40 hashtag candidates through LLM proxy prompt call."""
        response = await self.llm_client.post(
            f"{self.llm_proxy_url}/v1/llm/proxy/chat",
            json={
                "provider": "deepseek",
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Return JSON array with exactly 40 hashtag strings."},
                    {"role": "user", "content": f"text={core_text}; keywords={keywords}"},
                ],
                "response_format": "json",
                "temperature": 0.2,
                "max_tokens": 1200,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        output = payload.get("output", [])

        if isinstance(output, dict):
            output = output.get("hashtags", [])
        if not isinstance(output, list):
            output = []

        normalized = [str(h) for h in output][:40]
        if len(normalized) < 40:
            normalized.extend([f"#{keywords[i % len(keywords)]}_{i}" for i in range(len(normalized), 40)])
        return normalized[:40]
