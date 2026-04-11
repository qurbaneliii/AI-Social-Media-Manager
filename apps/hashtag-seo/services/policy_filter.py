# FILE: apps/hashtag-seo/services/policy_filter.py
from __future__ import annotations

import re

from redis.asyncio import Redis


class PolicyFilter:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    async def process(self, platform: str, banned_tags: list[str], tokens: list[str]) -> list[str]:
        """Reject globally banned tags and platform-specific blocked regex patterns from Redis."""
        blocked_raw = await self.redis_client.get(f"aria:policy:banned_tags:{platform}")
        blocked_patterns = blocked_raw.split("|") if blocked_raw else []
        banned_set = {t.lower().lstrip("#") for t in banned_tags}

        safe: list[str] = []
        for token in tokens:
            if token in banned_set:
                continue
            if any(re.search(pattern, token) for pattern in blocked_patterns if pattern):
                continue
            safe.append(token)
        return safe
