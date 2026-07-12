from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    DATABASE_URL: str | None = None
    JWT_SECRET: str | None = None
    ARIA_JWT_ISSUER: str = "aria-frontend"
    ARIA_JWT_AUDIENCE: str = "aria-api"
    ARIA_ENV: Literal["development", "test", "production"] = "production"
    ARIA_TEST_AUTH_ENABLED: bool = False
    AI_MOCK_MODE: bool = False
    CORS_ORIGINS: str = ""
    DATABASE_POOL_MIN_SIZE: int = 1
    DATABASE_POOL_MAX_SIZE: int = 5
    DATABASE_COMMAND_TIMEOUT_SECONDS: float = 15.0

    @property
    def test_auth_enabled(self) -> bool:
        return self.ARIA_ENV == "test" and self.ARIA_TEST_AUTH_ENABLED


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
