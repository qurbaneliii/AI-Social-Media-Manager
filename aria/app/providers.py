# filename: app/providers.py
# purpose: HTTPX-based LLM provider adapters with a unified async interface and consistent error handling.
# dependencies: os, abc, httpx, typing

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import httpx


class ProviderError(Exception):
    """Raised when a provider request fails with HTTP or protocol errors."""


class BaseLLMProvider(ABC):
    """Abstract provider contract for JSON-oriented text generation."""

    provider_name: str

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key or ""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int) -> str:
        """Generate JSON text for a prompt."""

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise ProviderError(f"{self.provider_name}: missing API key")

    @staticmethod
    def _raise_for_error(provider_name: str, response: httpx.Response) -> None:
        if 400 <= response.status_code:
            raise ProviderError(
                f"{provider_name}: HTTP {response.status_code} - {response.text}"
            )


class DeepSeekProvider(BaseLLMProvider):
    """Primary provider using DeepSeek chat completions in JSON mode."""

    provider_name = "deepseek"
    _url = "https://api.deepseek.com/v1/chat/completions"
    _model = "deepseek-chat"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self._model,
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
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self._url, headers=headers, json=payload)
            self._raise_for_error(self.provider_name, response)
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_name}: HTTP transport error - {exc}") from exc
        except (KeyError, ValueError, TypeError) as exc:
            raise ProviderError(f"{self.provider_name}: invalid response payload") from exc


class OpenAIProvider(BaseLLMProvider):
    """Fallback provider using OpenAI chat completions."""

    provider_name = "openai"
    _url = "https://api.openai.com/v1/chat/completions"
    _model = "gpt-4o-mini"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self._model,
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
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self._url, headers=headers, json=payload)
            self._raise_for_error(self.provider_name, response)
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_name}: HTTP transport error - {exc}") from exc
        except (KeyError, ValueError, TypeError) as exc:
            raise ProviderError(f"{self.provider_name}: invalid response payload") from exc


class AnthropicProvider(BaseLLMProvider):
    """Fallback provider using Anthropic Messages API."""

    provider_name = "anthropic"
    _url = "https://api.anthropic.com/v1/messages"
    _model = "claude-haiku-4-5-20251001"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": "Return only valid JSON.",
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self._url, headers=headers, json=payload)
            self._raise_for_error(self.provider_name, response)
            data = response.json()
            content = data.get("content", [])
            if not content or "text" not in content[0]:
                raise ProviderError(f"{self.provider_name}: malformed response content")
            return str(content[0]["text"])
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_name}: HTTP transport error - {exc}") from exc
        except (KeyError, ValueError, TypeError) as exc:
            raise ProviderError(f"{self.provider_name}: invalid response payload") from exc


class MistralProvider(BaseLLMProvider):
    """Fallback provider using Mistral chat completions."""

    provider_name = "mistral"
    _url = "https://api.mistral.ai/v1/chat/completions"
    _model = "mistral-small-latest"

    async def generate(self, prompt: str, max_tokens: int) -> str:
        self._ensure_api_key()
        payload = {
            "model": self._model,
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
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self._url, headers=headers, json=payload)
            self._raise_for_error(self.provider_name, response)
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_name}: HTTP transport error - {exc}") from exc
        except (KeyError, ValueError, TypeError) as exc:
            raise ProviderError(f"{self.provider_name}: invalid response payload") from exc


def build_default_provider_chain() -> list[BaseLLMProvider]:
    """Construct provider chain in required failover order."""
    return [
        DeepSeekProvider(os.getenv("DEEPSEEK_API_KEY")),
        OpenAIProvider(os.getenv("OPENAI_API_KEY")),
        AnthropicProvider(os.getenv("ANTHROPIC_API_KEY")),
        MistralProvider(os.getenv("MISTRAL_API_KEY")),
    ]
