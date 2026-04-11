# filename: api/llm_proxy.py
# purpose: LLM proxy endpoint exposing provider_used and cached response metadata.
# dependencies: json, fastapi, pydantic, app.cache, app.router

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.cache import SemanticCache
from app.router import LLMRouter

router = APIRouter()


class LLMProxyChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=512, ge=32, le=4096)


@router.post("/chat")
async def llm_proxy_chat(payload: LLMProxyChatRequest, request: Request) -> dict[str, Any]:
    cache: SemanticCache = request.app.state.semantic_cache
    llm_router: LLMRouter = request.app.state.llm_router

    cache_key = json.dumps(
        {
            "tenant_id": payload.company_id,
            "module": "llm_proxy_chat",
            "payload": {
                "prompt": payload.prompt,
                "max_tokens": payload.max_tokens,
            },
        },
        sort_keys=True,
    )

    cached_content = await cache.get(cache_key)
    if cached_content is not None:
        parsed = json.loads(cached_content)
        return {
            "content": parsed.get("content", ""),
            "provider_used": parsed.get("provider_used", "cache"),
            "cached": True,
        }

    generated = await llm_router.generate_with_provider(
        tenant_id=payload.company_id,
        prompt=payload.prompt,
        max_tokens=payload.max_tokens,
    )

    response = {
        "content": generated["content"],
        "provider_used": generated["provider_used"],
        "cached": False,
    }
    await cache.set(cache_key, json.dumps(response, separators=(",", ":")))
    return response
