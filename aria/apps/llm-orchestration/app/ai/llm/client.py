from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import LLMSettings
from .errors import LLMError
from .types import LLMMessage

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Central LLM gateway with mock mode and structured output validation."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings()

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        output_model: type[T],
        *,
        mock_factory: Callable[[], dict[str, Any]] | None = None,
        temperature: float | None = None,
    ) -> T:
        if self.settings.use_mock_mode:
            if mock_factory is None:
                raise LLMError("Mock mode requires a mock_factory for structured generation.")
            log.info("llm_mock_response", model=self.settings.openai_model, schema=output_model.__name__)
            return output_model.model_validate(mock_factory())

        return await self._call_openai_structured(messages, output_model, temperature=temperature)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, LLMError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _call_openai_structured(
        self,
        messages: list[LLMMessage],
        output_model: type[T],
        *,
        temperature: float | None = None,
    ) -> T:
        payload = {
            "model": self.settings.openai_model,
            "temperature": self.settings.ai_temperature if temperature is None else temperature,
            "messages": [message.model_dump() for message in messages],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.settings.ai_request_timeout_seconds) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if response.status_code >= 400:
                raise LLMError(f"OpenAI request failed with status {response.status_code}")
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            log.info(
                "llm_structured_response",
                model=self.settings.openai_model,
                schema=output_model.__name__,
                usage=data.get("usage", {}),
            )
            return output_model.model_validate(parsed)
        except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as exc:
            raise LLMError(f"OpenAI structured response could not be parsed as {output_model.__name__}") from exc

