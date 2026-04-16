# FILE: apps/hashtag-seo/services/llm_candidate_generator.py
from __future__ import annotations

import asyncio
import json
import re

import httpx


RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _sanitize_text(value: str, max_chars: int) -> str:
    compact = " ".join(value.replace("\x00", " ").split()).strip()
    return compact[:max_chars]


def _strip_json_fences(value: str) -> str:
    return value.strip().replace("```json", "").replace("```", "").strip()


def _normalize_hashtag_token(value: str) -> str:
    token = value.strip().lstrip("#")
    token = re.sub(r"\s+", "", token)
    token = re.sub(r"[^A-Za-z0-9_]", "", token)
    return token.lower()


class LlmCandidateGenerator:
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
                    raise ValueError("LLM proxy hashtag response is not a JSON object")
                return data
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < self.max_retries:
                    await asyncio.sleep(min(1.0 * (2**attempt), 8.0))
                    continue
                raise

        raise RuntimeError("LLM proxy hashtag generation failed after retries")

    @staticmethod
    def _parse_hashtags(raw_content: str) -> list[str]:
        normalized = _strip_json_fences(raw_content)
        payload = json.loads(normalized)

        if isinstance(payload, dict):
            hashtags = payload.get("hashtags", [])
        elif isinstance(payload, list):
            hashtags = payload
        else:
            raise ValueError("LLM hashtag payload must be a JSON object or array")

        if not isinstance(hashtags, list):
            raise ValueError("LLM hashtag payload missing list of hashtags")
        return [str(tag) for tag in hashtags]

    async def process(self, company_id: str, core_text: str, keywords: list[str]) -> list[str]:
        """Generate exactly 40 hashtag candidates through LLM proxy prompt call."""
        if not company_id:
            raise ValueError("company_id is required for hashtag generation")

        sanitized_text = _sanitize_text(core_text, 2500)
        sanitized_keywords = [_sanitize_text(str(keyword), 80) for keyword in keywords if str(keyword).strip()][:30]
        if not sanitized_text:
            raise ValueError("core_text is required for hashtag generation")

        prompt = (
            "Return strict JSON only with shape {\"hashtags\": [string, ...]}. "
            "Generate exactly 40 unique hashtag tokens without leading # and without spaces. "
            f"core_text={sanitized_text}; keywords={json.dumps(sanitized_keywords)}"
        )
        payload = await self._post_with_retry({"company_id": company_id, "prompt": prompt, "max_tokens": 1200})

        raw_content = payload.get("content")
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ValueError("LLM proxy returned empty hashtag content")

        raw_hashtags = self._parse_hashtags(raw_content)
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in raw_hashtags:
            token = _normalize_hashtag_token(raw)
            if not token or token in seen:
                continue
            seen.add(token)
            normalized.append(token)
            if len(normalized) == 40:
                break

        if len(normalized) < 40:
            raise ValueError(f"LLM returned insufficient unique hashtags: {len(normalized)}")

        return normalized
