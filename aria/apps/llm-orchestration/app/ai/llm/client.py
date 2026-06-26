from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import LLMSettings
from .errors import LLMError
from .types import LLMMessage, LLMMetadata

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Central LLM gateway with mock mode and structured output validation."""

    def __init__(
        self,
        settings: LLMSettings | None = None,
        metadata_hook: Callable[[LLMMetadata], None] | None = None,
    ) -> None:
        self.settings = settings or LLMSettings()
        self.metadata_hook = metadata_hook

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
            self._emit_metadata(
                LLMMetadata(
                    model=self.settings.openai_model,
                    mock_mode=True,
                    extra={"schema": output_model.__name__, "estimated_cost_usd": 0.0},
                )
            )
            return output_model.model_validate(mock_factory())

        return await self._call_openai_structured(messages, output_model, temperature=temperature)

    async def _call_openai_structured(
        self,
        messages: list[LLMMessage],
        output_model: type[T],
        *,
        temperature: float | None = None,
    ) -> T:
        attempts = max(1, self.settings.ai_max_retries + 1)
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.HTTPError, LLMError)),
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        ):
            with attempt:
                return await self._request_openai_structured(messages, output_model, temperature=temperature)

        raise LLMError("OpenAI structured request failed without returning a response.")

    async def _request_openai_structured(
        self,
        messages: list[LLMMessage],
        output_model: type[T],
        *,
        temperature: float | None = None,
    ) -> T:
        schema_instruction = LLMMessage(
            role="system",
            content=(
                "Return only valid JSON that exactly matches this JSON Schema. "
                "Use arrays for array fields, objects for object fields, strings for string fields, "
                "numbers for numeric fields, booleans for boolean fields, and null only when allowed. "
                f"JSON Schema:\n{json.dumps(output_model.model_json_schema(), default=str)}"
            ),
        )
        payload = {
            "model": self.settings.openai_model,
            "temperature": self.settings.ai_temperature if temperature is None else temperature,
            "messages": [message.model_dump() for message in [*messages, schema_instruction]],
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
            self._emit_metadata(
                LLMMetadata(
                    model=self.settings.openai_model,
                    mock_mode=False,
                    token_usage=data.get("usage", {}),
                    raw_response_id=data.get("id"),
                    extra={
                        "schema": output_model.__name__,
                        "estimated_cost_usd": None,
                    },
                )
            )
            return output_model.model_validate(parsed)
        except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as exc:
            raise LLMError(f"OpenAI structured response could not be parsed as {output_model.__name__}") from exc

    def _emit_metadata(self, metadata: LLMMetadata) -> None:
        if self.metadata_hook is None:
            return
        try:
            self.metadata_hook(metadata)
        except Exception:
            log.exception("llm_metadata_hook_failed", model=metadata.model)
