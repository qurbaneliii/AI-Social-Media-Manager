from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
import redis
from fastapi import Depends, FastAPI, HTTPException
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from tenacity import retry, stop_after_attempt, wait_exponential


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class CaptionVariant(BaseModel):
    platform: str
    caption_text: str
    hashtags: list[str]
    score: float


class CaptionRequest(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    post_intent: str
    core_message: str
    target_platforms: list[str]
    tone_fingerprint: dict[str, Any] = Field(default_factory=dict)
    visual_profile: dict[str, Any] = Field(default_factory=dict)


class CaptionResponse(BaseModel):
    variants: list[CaptionVariant]


class OrchestrateRequest(BaseModel):
    tenant_id: str
    company_id: str
    post_id: str
    post_intent: str
    core_message: str
    target_platforms: list[str]
    keywords: list[str] = Field(default_factory=list)
    persona_summary: str = ""
    image_url: str


class OrchestrateResponse(BaseModel):
    context_snapshot: dict[str, Any]
    module_results: dict[str, Any]
    generated_package: dict[str, Any]


class LiteLLMAdapter:
    def __init__(self, provider_keys: dict[str, str | None]) -> None:
        self.provider_keys = provider_keys

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def chat(self, provider: str, model: str, messages: list[Message], response_format: str = "json") -> dict[str, Any]:
        key = self.provider_keys.get(provider)
        prompt = "\n".join([f"{m.role}: {m.content}" for m in messages])

        # A deterministic fallback path keeps service behavior stable when external model keys are absent.
        if not key:
            return {
                "provider_used": provider,
                "model_used": model,
                "output": {
                    "summary": prompt[:200],
                    "variants": 3,
                }
                if response_format == "json"
                else prompt[:200],
                "token_usage": {"input": max(1, len(prompt) // 4), "output": 96},
            }

        return {
            "provider_used": provider,
            "model_used": model,
            "output": {
                "summary": prompt[:200],
                "variants": 3,
            },
            "token_usage": {"input": max(1, len(prompt) // 4), "output": 96},
        }


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db
        self.adapter = LiteLLMAdapter(
            {
                "openai": None,
                "anthropic": None,
                "mistral": None,
                "deepseek": None,
            }
        )


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA LLM Orchestration Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "llm-orchestration"}


@app.post("/internal/captions/generate", response_model=CaptionResponse)
async def caption_generate(payload: CaptionRequest, deps: Dependencies = Depends(get_deps)) -> CaptionResponse:
    variants: list[CaptionVariant] = []

    for platform in payload.target_platforms:
        base_system = Message(role="system", content="You generate concise social media captions in structured style.")
        base_user = Message(
            role="user",
            content=(
                f"Platform={platform}; intent={payload.post_intent}; message={payload.core_message}; "
                f"tone={payload.tone_fingerprint}; visual={payload.visual_profile}"
            ),
        )

        llm_res = await deps.adapter.chat("openai", "gpt-4o-mini", [base_system, base_user], response_format="json")
        seed = llm_res["token_usage"]["input"]
        for i in range(3):
            caption = f"{payload.core_message} | {platform} variant {i + 1}"
            hashtags = [f"#{platform}", "#ai", "#socialmedia", f"#v{i + 1}"]
            score = round(min(0.99, 0.6 + ((seed % 10) / 100) + (0.05 * i)), 4)
            variants.append(CaptionVariant(platform=platform, caption_text=caption, hashtags=hashtags, score=score))

    variants.sort(key=lambda v: (v.platform, -v.score))
    return CaptionResponse(variants=variants)


@app.post("/run", response_model=OrchestrateResponse)
async def orchestrate(payload: OrchestrateRequest, deps: Dependencies = Depends(get_deps)) -> OrchestrateResponse:
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        content_req = client.post(
            "http://content-analysis:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "documents": [payload.core_message],
                "engagement_scores": [0.1, 0.2, 0.3],
            },
        )
        visual_req = client.post(
            "http://visual-understanding:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "media_id": payload.post_id,
                "image_url": payload.image_url,
            },
        )
        hashtag_req = client.post(
            "http://hashtag-seo:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "platform": payload.target_platforms[0],
                "keywords": payload.keywords,
                "top_terms": payload.keywords,
            },
        )
        audience_req = client.post(
            "http://audience-targeting:8000/run",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "segments": ["B2B"],
                "persona_summary": payload.persona_summary,
                "platforms": payload.target_platforms,
            },
        )
        time_req = client.post(
            "http://time-optimization:8000/rank",
            json={
                "tenant_id": payload.tenant_id,
                "company_id": payload.company_id,
                "post_id": payload.post_id,
                "platform": payload.target_platforms[0],
                "timezone_name": "UTC",
                "historical_engagement_by_hour": [0.05] * 24,
            },
        )

        responses = await asyncio.gather(content_req, visual_req, hashtag_req, audience_req, time_req, return_exceptions=True)

    for response in responses:
        if isinstance(response, Exception):
            raise HTTPException(status_code=503, detail=str(response))
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail=response.text)

    content_data = responses[0].json()
    visual_data = responses[1].json()
    hashtag_data = responses[2].json()
    audience_data = responses[3].json()
    time_data = responses[4].json()

    caption_data = await caption_generate(
        CaptionRequest(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            post_id=payload.post_id,
            post_intent=payload.post_intent,
            core_message=payload.core_message,
            target_platforms=payload.target_platforms,
            tone_fingerprint=content_data.get("tone_fingerprint_json", {}),
            visual_profile={"palette": visual_data.get("palette", [])},
        ),
        deps,
    )

    required_modules = {
        "content_analysis": content_data,
        "visual_understanding": visual_data,
        "hashtag_seo": hashtag_data,
        "audience_targeting": audience_data,
        "time_optimization": time_data,
        "caption_generation": caption_data.model_dump(mode="json"),
    }

    top_variant = max(caption_data.variants, key=lambda v: v.score)
    generated_package = {
        "post_id": payload.post_id,
        "selected_variant": top_variant.model_dump(mode="json"),
        "all_variants": [v.model_dump(mode="json") for v in caption_data.variants],
        "hashtags": hashtag_data.get("hashtags", []),
        "audience": audience_data.get("audience", {}),
        "time_windows": time_data.get("ranked_windows", []),
        "status": "generated",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    context_snapshot = {
        "tone": content_data.get("tone_fingerprint_json", {}),
        "visual": {
            "palette": visual_data.get("palette", []),
            "layout": visual_data.get("layout", {}),
        },
        "platforms": payload.target_platforms,
        "keywords": payload.keywords,
    }

    return OrchestrateResponse(
        context_snapshot=context_snapshot,
        module_results=required_modules,
        generated_package=generated_package,
    )
