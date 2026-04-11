# FILE: apps/audience-targeting/services/platform_segment_mapper.py
from __future__ import annotations

import json

from redis.asyncio import Redis


class PlatformSegmentMapper:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

    async def process(self, platforms: list[str], segments: list[str]) -> dict[str, list[str]]:
        """Map generic segments into platform-specific taxonomy dictionaries from Redis."""
        out: dict[str, list[str]] = {}
        for platform in platforms:
            raw = await self.redis_client.get(f"aria:taxonomy:{platform}")
            taxonomy = json.loads(raw) if raw else {}
            mapped: list[str] = []
            for segment in segments:
                mapped.extend(taxonomy.get(segment, [segment]))
            out[platform] = list(dict.fromkeys(mapped))[:10]
        return out
