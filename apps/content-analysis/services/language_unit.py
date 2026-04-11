# FILE: apps/content-analysis/services/language_unit.py
from __future__ import annotations

from dataclasses import dataclass

import httpx
from langdetect import DetectorFactory, detect_langs

from exceptions import LocaleUncertainError

DetectorFactory.seed = 0


@dataclass
class LanguageResult:
    texts: list[str]
    translated: bool


class LanguageDetectionUnit:
    def __init__(self, llm_client: httpx.AsyncClient, llm_proxy_url: str, min_confidence: float) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url
        self.min_confidence = min_confidence

    async def process(self, texts: list[str], target_locale: str) -> LanguageResult:
        """Detect language confidence and optionally auto-translate non-English text."""
        joined = "\n".join(texts[:20])
        probs = detect_langs(joined)
        top = probs[0]
        if top.prob < self.min_confidence:
            raise LocaleUncertainError()

        if top.lang == "en" or target_locale == "en":
            return LanguageResult(texts=texts, translated=False)

        translated: list[str] = []
        for text in texts:
            response = await self.llm_client.post(
                f"{self.llm_proxy_url}/v1/llm/proxy/chat",
                json={
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Translate to English preserving meaning."},
                        {"role": "user", "content": text},
                    ],
                    "response_format": "text",
                    "temperature": 0.0,
                    "max_tokens": 512,
                },
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            translated.append(str(data.get("output", text)))

        return LanguageResult(texts=translated, translated=True)
