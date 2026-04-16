# FILE: apps/content-analysis/services/language_unit.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx
from langdetect import DetectorFactory, detect_langs

from exceptions import LocaleUncertainError

DetectorFactory.seed = 0
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _sanitize_text(value: str, max_chars: int) -> str:
    compact = " ".join(value.replace("\x00", " ").split()).strip()
    return compact[:max_chars]


def _strip_markdown_fences(value: str) -> str:
    return value.strip().replace("```", "").strip()


@dataclass
class LanguageResult:
    texts: list[str]
    translated: bool


class LanguageDetectionUnit:
    def __init__(
        self,
        llm_client: httpx.AsyncClient,
        llm_proxy_url: str,
        min_confidence: float,
        timeout_seconds: float = 45.0,
        max_retries: int = 2,
    ) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url
        self.min_confidence = min_confidence
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
                    raise ValueError("LLM proxy translation response is not a JSON object")
                return data
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < self.max_retries:
                    await asyncio.sleep(min(1.0 * (2**attempt), 8.0))
                    continue
                raise

        raise RuntimeError("LLM translation request failed after retries")

    async def _translate_text(self, company_id: str, text: str) -> str:
        prompt = (
            "Translate the following content to English while preserving meaning and tone. "
            "Return only translated plain text without explanations or markdown. "
            f"text={text}"
        )

        payload = await self._post_with_retry({"company_id": company_id, "prompt": prompt, "max_tokens": 512})
        raw_content = payload.get("content")
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ValueError("LLM proxy returned empty translation content")

        translated = _strip_markdown_fences(raw_content)
        if not translated:
            raise ValueError("LLM proxy returned blank translation text")
        return translated

    async def process(self, company_id: str, texts: list[str], target_locale: str) -> LanguageResult:
        """Detect language confidence and optionally auto-translate non-English text."""
        if not texts:
            return LanguageResult(texts=texts, translated=False)

        joined = "\n".join(texts[:20])
        try:
            probs = detect_langs(joined)
        except Exception as exc:  # noqa: BLE001
            raise LocaleUncertainError() from exc

        if not probs:
            raise LocaleUncertainError()

        top = probs[0]
        if top.prob < self.min_confidence:
            raise LocaleUncertainError()

        if top.lang == "en" or target_locale == "en":
            return LanguageResult(texts=texts, translated=False)

        translated: list[str] = []
        for text in texts:
            sanitized = _sanitize_text(text, 4000)
            if not sanitized:
                translated.append("")
                continue
            translated.append(await self._translate_text(company_id, sanitized))

        return LanguageResult(texts=translated, translated=True)
