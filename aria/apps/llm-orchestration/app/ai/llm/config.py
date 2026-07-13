from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    ai_mock_mode: bool = Field(default=False, alias="AI_MOCK_MODE")
    ai_temperature: float = Field(default=0.4, ge=0.0, le=1.0, alias="AI_TEMPERATURE")
    ai_max_retries: int = Field(default=2, ge=0, le=5, alias="AI_MAX_RETRIES")
    ai_request_timeout_seconds: float = Field(default=45.0, gt=0, alias="AI_REQUEST_TIMEOUT_SECONDS")

    @property
    def use_mock_mode(self) -> bool:
        return self.ai_mock_mode

