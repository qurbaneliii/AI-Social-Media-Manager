# filename: app/router.py
# purpose: LLM request router with ordered fallbacks, per-provider circuit breakers, and concurrency controls.
# dependencies: asyncio, logging, time, dataclasses, typing, app.providers

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.providers import BaseLLMProvider, ProviderError, build_default_provider_chain

logger = logging.getLogger(__name__)


@dataclass
class ProviderCircuitState:
    failure_timestamps: list[float] = field(default_factory=list)
    last_failure_timestamp: float | None = None
    last_attempt_timestamp: float | None = None
    opened_at: float | None = None
    state: str = "closed"  # closed | open | half-open


class LLMRouter:
    """Routes LLM calls through ordered providers with circuit-breaker failover."""

    def __init__(
        self,
        providers: list[BaseLLMProvider],
        global_inflight_cap: int = 300,
        tenant_inflight_cap: int = 10,
    ) -> None:
        self.providers = providers
        self.global_semaphore = asyncio.Semaphore(global_inflight_cap)
        self.tenant_inflight_cap = tenant_inflight_cap
        self.tenant_semaphores: dict[str, asyncio.Semaphore] = {}
        self.tenant_lock = asyncio.Lock()
        self.circuits: dict[str, ProviderCircuitState] = {
            p.provider_name: ProviderCircuitState() for p in providers
        }

    async def _get_tenant_semaphore(self, tenant_id: str) -> asyncio.Semaphore:
        async with self.tenant_lock:
            if tenant_id not in self.tenant_semaphores:
                self.tenant_semaphores[tenant_id] = asyncio.Semaphore(self.tenant_inflight_cap)
            return self.tenant_semaphores[tenant_id]

    def _trim_failures(self, state: ProviderCircuitState, now: float) -> None:
        state.failure_timestamps = [ts for ts in state.failure_timestamps if (now - ts) <= 30.0]

    def _refresh_state(self, provider_name: str, now: float) -> None:
        state = self.circuits[provider_name]
        if state.state == "open" and state.opened_at is not None and (now - state.opened_at) >= 60.0:
            last_attempt = state.last_attempt_timestamp or 0.0
            if (now - last_attempt) >= 60.0:
                old = state.state
                state.state = "closed"
                state.opened_at = None
                state.failure_timestamps.clear()
                state.last_failure_timestamp = None
                logger.info(
                    "provider=%s breaker_state_change %s->%s",
                    provider_name,
                    old,
                    state.state,
                )

    def _can_attempt(self, provider_name: str, now: float) -> bool:
        state = self.circuits[provider_name]
        if state.state == "open" and state.opened_at is not None and (now - state.opened_at) >= 60.0:
            old = state.state
            state.state = "half-open"
            logger.info("provider=%s breaker_state_change %s->%s", provider_name, old, state.state)
            return True

        self._refresh_state(provider_name, now)
        state = self.circuits[provider_name]
        return state.state != "open"

    def _record_success(self, provider_name: str) -> None:
        state = self.circuits[provider_name]
        old = state.state
        state.failure_timestamps.clear()
        state.last_failure_timestamp = None
        state.opened_at = None
        state.state = "closed"
        if old != state.state:
            logger.info("provider=%s breaker_state_change %s->%s", provider_name, old, state.state)

    def _record_failure(self, provider_name: str, now: float) -> None:
        state = self.circuits[provider_name]
        state.last_failure_timestamp = now
        state.failure_timestamps.append(now)
        self._trim_failures(state, now)

        should_open = len(state.failure_timestamps) >= 5
        if state.state == "half-open" and should_open:
            old = state.state
            state.state = "open"
            state.opened_at = now
            logger.info("provider=%s breaker_state_change %s->%s", provider_name, old, state.state)
            return

        if state.state == "closed" and should_open:
            old = state.state
            state.state = "open"
            state.opened_at = now
            logger.info("provider=%s breaker_state_change %s->%s", provider_name, old, state.state)

    async def generate(self, tenant_id: str, prompt: str, max_tokens: int) -> str:
        """Generate response via the first available provider in failover order."""
        tenant_sem = await self._get_tenant_semaphore(tenant_id)

        async with self.global_semaphore:
            async with tenant_sem:
                last_error: ProviderError | None = None
                for provider in self.providers:
                    provider_name = provider.provider_name
                    now = time.time()
                    state = self.circuits[provider_name]

                    if not self._can_attempt(provider_name, now):
                        logger.info(
                            "tenant=%s provider=%s skip reason=breaker_open",
                            tenant_id,
                            provider_name,
                        )
                        continue

                    state.last_attempt_timestamp = now
                    logger.info("tenant=%s provider=%s attempt", tenant_id, provider_name)
                    try:
                        result = await provider.generate(prompt=prompt, max_tokens=max_tokens)
                        self._record_success(provider_name)
                        logger.info("tenant=%s provider=%s success", tenant_id, provider_name)
                        return result
                    except ProviderError as exc:
                        self._record_failure(provider_name, now)
                        logger.info(
                            "tenant=%s provider=%s failure error=%s",
                            tenant_id,
                            provider_name,
                            str(exc),
                        )
                        last_error = exc
                        logger.info(
                            "tenant=%s provider=%s fallback_next=true",
                            tenant_id,
                            provider_name,
                        )
                        continue

                raise last_error or ProviderError("router: all providers unavailable")

    def get_status(self) -> dict[str, dict[str, Any]]:
        """Return operational status for each provider breaker."""
        now = time.time()
        status: dict[str, dict[str, Any]] = {}

        for provider in self.providers:
            provider_name = provider.provider_name
            self._refresh_state(provider_name, now)
            state = self.circuits[provider_name]
            self._trim_failures(state, now)
            status[provider_name] = {
                "state": state.state,
                "failure_count": len(state.failure_timestamps),
                "last_failure_timestamp": state.last_failure_timestamp,
            }

        return status


def build_default_router() -> LLMRouter:
    """Build router with required provider chain and concurrency limits."""
    return LLMRouter(providers=build_default_provider_chain())
