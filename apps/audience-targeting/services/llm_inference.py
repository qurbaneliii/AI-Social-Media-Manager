# FILE: apps/audience-targeting/services/llm_inference.py
from __future__ import annotations

import asyncio
import json
import logging

import httpx


logger = logging.getLogger(__name__)
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _sanitize_text(value: str, max_chars: int) -> str:
    compact = " ".join(value.replace("\x00", " ").split()).strip()
    return compact[:max_chars]


def _parse_json_from_content(raw_content: str) -> dict:
    normalized = raw_content.strip()
    normalized = normalized.replace("```json", "").replace("```", "").strip()

    data = json.loads(normalized)
    if not isinstance(data, dict):
        raise ValueError("LLM audience response must be a JSON object")
    return data


class LlmInference:
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
                    raise ValueError("LLM proxy response is not a JSON object")
                return data
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < self.max_retries:
                    await asyncio.sleep(min(1.0 * (2**attempt), 8.0))
                    continue
                raise

        raise RuntimeError("LLM proxy audience request failed after retries")

    async def process(self, company_id: str, campaign_context: str, segments: list[str]) -> dict:
        """Infer psychographic audience profile via structured LLM JSON output."""
        if not company_id:
            raise ValueError("company_id is required for audience LLM inference")

        sanitized_context = _sanitize_text(campaign_context, 2000)
        sanitized_segments = [_sanitize_text(str(segment), 200) for segment in segments if str(segment).strip()][:50]
        if not sanitized_context or not sanitized_segments:
            raise ValueError("campaign_context and segments are required for audience LLM inference")

        prompt = (
            "Return strict JSON only with shape: "
            '{"age_range":{"min_age":int,"max_age":int},"psychographics":{string:number},"confidence":number}. '
            "confidence must be 0..1. Use provided campaign context and audience segments. "
            f"campaign_context={sanitized_context}; segments={json.dumps(sanitized_segments)}"
        )

        response_payload = await self._post_with_retry(
            {
                "company_id": company_id,
                "prompt": prompt,
                "max_tokens": 800,
            }
        )

        raw_content = response_payload.get("content")
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ValueError("LLM proxy returned empty audience content")

        output = _parse_json_from_content(raw_content)
        age_range = output.get("age_range")
        if not isinstance(age_range, dict):
            raise ValueError("Audience response missing age_range object")

        min_age = int(age_range.get("min_age"))
        max_age = int(age_range.get("max_age"))
        if min_age > max_age:
            raise ValueError("Audience response has invalid age_range bounds")

        psychographics = output.get("psychographics", {})
        if psychographics is None:
            psychographics = {}
        if not isinstance(psychographics, dict):
            raise ValueError("Audience response psychographics must be an object")

        normalized_psychographics: dict[str, float] = {}
        for key, value in psychographics.items():
            if not str(key).strip():
                continue
            normalized_psychographics[str(key)] = float(value)

        confidence = float(output.get("confidence"))
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("Audience response confidence must be between 0 and 1")

        logger.info(
            "audience_llm_response_parsed provider=%s",
            response_payload.get("provider_used", "unknown"),
        )

        return {
            "age_range": {"min_age": min_age, "max_age": max_age},
            "psychographics": normalized_psychographics,
            "confidence": confidence,
        }
