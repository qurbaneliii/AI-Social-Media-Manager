# FILE: apps/caption-generation/services/provider_router.py
from __future__ import annotations

import asyncio
import json

import httpx
from prompt_templates import build_caption_generation_prompt


RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _strip_json_fences(value: str) -> str:
    return value.strip().replace("```json", "").replace("```", "").strip()


def _messages_to_prompt(messages: list[dict]) -> str:
    parts: list[str] = []
    for message in messages:
        role = str(message.get("role", "user")).upper()
        content = message.get("content", "")
        content_text = " ".join(str(content).split()).strip()
        if content_text:
            parts.append(f"{role}: {content_text}")
    return "\n".join(parts)


class ProviderRouter:
    def __init__(
        self,
        llm_client: httpx.AsyncClient,
        llm_proxy_url: str,
        timeout_seconds: float = 45.0,
        max_retries: int = 2,
    ) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url
        self.timeout_seconds = max(5.0, timeout_seconds)
        self.max_retries = max(0, max_retries)

    async def _post_with_retry(self, payload: dict) -> dict:
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.llm_client.post(
                    f"{self.llm_proxy_url}/v1/llm/proxy/chat",
                    json=payload,
                    timeout=self.timeout_seconds,
                )

                if response.status_code >= 400:
                    if attempt < self.max_retries and response.status_code in RETRYABLE_STATUS:
                        await asyncio.sleep(min(1.0 * (2**attempt), 8.0))
                        continue
                    response.raise_for_status()

                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("LLM proxy caption response is not a JSON object")
                return data
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < self.max_retries:
                    await asyncio.sleep(min(1.0 * (2**attempt), 8.0))
                    continue
                raise

        raise RuntimeError("LLM proxy caption request failed after retries")

    @staticmethod
    def _parse_variants(raw_content: str) -> list[dict]:
        normalized = _strip_json_fences(raw_content)
        payload = json.loads(normalized)

        if isinstance(payload, dict):
            variants = payload.get("variants", [])
            if not variants and "caption_text" in payload:
                variants = [payload]
            if isinstance(variants, dict):
                variants = [variants]
        elif isinstance(payload, list):
            variants = payload
        else:
            raise ValueError("LLM caption payload must be JSON object or array")

        if not isinstance(variants, list):
            raise ValueError("LLM caption variants must be a list")

        normalized_variants: list[dict] = []
        for item in variants:
            if isinstance(item, dict):
                normalized_variants.append(item)

        if not normalized_variants:
            raise ValueError("LLM returned no valid caption variants")
        return normalized_variants

    async def process(self, context, company_id: str) -> list[dict]:
        """Generate caption variants through the centralized LLM proxy endpoint."""
        if not company_id:
            raise ValueError("company_id is required for caption generation")

        base_messages = build_caption_generation_prompt(context)
        prompt = _messages_to_prompt(base_messages)
        if not prompt:
            raise ValueError("Caption prompt is empty after normalization")

        payload = await self._post_with_retry(
            {
                "company_id": company_id,
                "prompt": prompt,
                "max_tokens": 1000,
            }
        )

        raw_content = payload.get("content")
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ValueError("LLM proxy returned empty caption content")

        return self._parse_variants(raw_content)
