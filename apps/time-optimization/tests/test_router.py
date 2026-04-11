# FILE: apps/time-optimization/tests/test_router.py
from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest

from router import router


@pytest.mark.asyncio
async def test_health() -> None:
    app = FastAPI()
    app.state.settings = type("S", (), {"service_version": "1.0.0"})()
    app.include_router(router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_payload() -> None:
    app = FastAPI()
    app.state.settings = type("S", (), {"service_version": "1.0.0"})()
    app.include_router(router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/run", json={"company_id": "bad"})
    assert response.status_code == 422
