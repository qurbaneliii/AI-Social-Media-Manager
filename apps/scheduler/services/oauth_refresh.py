# FILE: apps/scheduler/services/oauth_refresh.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx


class OAuthRefreshService:
    def __init__(self, llm_client: httpx.AsyncClient, llm_proxy_url: str) -> None:
        self.llm_client = llm_client
        self.llm_proxy_url = llm_proxy_url

    async def process(self, token_expires_at: datetime | None) -> bool:
        """Refresh OAuth token when expiry is within ten minutes from current time."""
        if token_expires_at is None:
            return False
        if token_expires_at - datetime.now(tz=timezone.utc) >= timedelta(minutes=10):
            return False

        response = await self.llm_client.post(
            f"{self.llm_proxy_url}/internal/oauth/refresh",
            json={"reason": "pre_publish_refresh"},
            timeout=15.0,
        )
        return response.status_code < 400
