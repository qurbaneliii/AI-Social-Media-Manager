from __future__ import annotations

from ai.llm import LLMClient
from ai.prompts import PromptRegistry


class BaseAgent:
    def __init__(self, llm_client: LLMClient, prompt_registry: PromptRegistry) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry

