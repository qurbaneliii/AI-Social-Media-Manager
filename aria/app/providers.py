# filename: app/providers.py
# purpose: HTTPX-based LLM provider adapters with a unified async interface and consistent error handling.
# dependencies: os, abc, httpx, typing

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx


class ProviderError(Exception):
    """Raised when a provider request fails with HTTP or protocol errors."""


RETRYABLE_HTTP_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _int_env(name: str, default: int, minimum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _float_env(name: str, default: float, minimum: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(minimum, float(raw))
    except ValueError:
        return default


class BaseLLMProvider(ABC):
    """Abstract provider contract for JSON-oriented text generation."""

    provider_name: str
    api_url: str
    default_model: str
    model_env_name: str

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key or ""
        self.timeout_seconds = _float_env("LLM_PROVIDER_TIMEOUT_SECONDS", 45.0, 5.0)
        self.max_retries = _int_env("LLM_PROVIDER_MAX_RETRIES", 2, 0)
        self.model = os.getenv(self.model_env_name, self.default_model)

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int) -> str:
        """Generate JSON text for a prompt."""

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise ProviderError(f"{self.provider_name}: missing API key")

    @staticmethod
    def _preview_error_text(text: str, max_chars: int = 500) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rstrip() + "..."

    async def _sleep_before_retry(self, attempt: int) -> None:
        delay_seconds = min(1.2 * (2 ** attempt), 8.0)
        await asyncio.sleep(delay_seconds)

    async def _request_json(self, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(self.api_url, headers=headers, json=payload)

                if response.status_code >= 400:
                    if attempt < self.max_retries and response.status_code in RETRYABLE_HTTP_STATUS:
                        await self._sleep_before_retry(attempt)
                        continue

                    detail = self._preview_error_text(response.text)
                    raise ProviderError(
                        f"{self.provider_name}: HTTP {response.status_code} - {detail}"
                    )

                try:
                    data = response.json()
                except ValueError as exc:
                    raise ProviderError(f"{self.provider_name}: invalid JSON response") from exc

                if not isinstance(data, dict):
                    raise ProviderError(f"{self.provider_name}: invalid response payload")

                return data
            except httpx.HTTPError as exc:
                if attempt < self.max_retries:
                    await self._sleep_before_retry(attempt)
                    continue
                raise ProviderError(f"{self.provider_name}: HTTP transport error - {exc}") from exc

        raise ProviderError(f"{self.provider_name}: request failed")

    @staticmethod
    def _extract_choice_message_content(provider_name: str, data: dict[str, Any]) -> str:
        try:
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise KeyError("choices")
            message = choices[0].get("message")
            if not isinstance(message, dict):
                raise KeyError("message")
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise KeyError("content")
            return content
        except (AttributeError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{provider_name}: invalid response payload") from exc


class DeepSeekProvider(BaseLLMProvider):
    """Primary provider using DeepSeek chat completions in JSON mode."""

    provider_name = "deepseek"
    api_url = "https://api.deepseek.com/v1/chat/completions"
    model_env_name = "DEEPSEEK_MODEL"
    default_model = "deepseek-chat"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = await self._request_json(headers, payload)
        return self._extract_choice_message_content(self.provider_name, data)


class OpenAIProvider(BaseLLMProvider):
    """Fallback provider using OpenAI chat completions."""

    provider_name = "openai"
    api_url = "https://api.openai.com/v1/chat/completions"
    model_env_name = "OPENAI_LLM_MODEL"
    default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = await self._request_json(headers, payload)
        return self._extract_choice_message_content(self.provider_name, data)


class AnthropicProvider(BaseLLMProvider):
    """Fallback provider using Anthropic Messages API."""

    provider_name = "anthropic"
    api_url = "https://api.anthropic.com/v1/messages"
    model_env_name = "ANTHROPIC_MODEL"
    default_model = "claude-3-5-haiku-latest"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": "Return only valid JSON.",
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        data = await self._request_json(headers, payload)
        try:
            content = data.get("content")
            if not isinstance(content, list) or not content:
                raise KeyError("content")
            first = content[0]
            if not isinstance(first, dict):
                raise KeyError("content[0]")
            text = first.get("text")
            if not isinstance(text, str) or not text.strip():
                raise KeyError("text")
            return text
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"{self.provider_name}: invalid response payload") from exc


class MistralProvider(BaseLLMProvider):
    """Fallback provider using Mistral chat completions."""

    provider_name = "mistral"
    api_url = "https://api.mistral.ai/v1/chat/completions"
    model_env_name = "MISTRAL_MODEL"
    default_model = "mistral-small-latest"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = await self._request_json(headers, payload)
        return self._extract_choice_message_content(self.provider_name, data)


def build_default_provider_chain() -> list[BaseLLMProvider]:
    """Construct provider chain in required failover order."""
    chain = [
        DeepSeekProvider(os.getenv("DEEPSEEK_API_KEY")),
        OpenAIProvider(os.getenv("OPENAI_API_KEY")),
        AnthropicProvider(os.getenv("ANTHROPIC_API_KEY")),
        MistralProvider(os.getenv("MISTRAL_API_KEY")),
    ]
    return [provider for provider in chain if provider.api_key]
