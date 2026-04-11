# FILE: apps/content-analysis/tests/test_router.py
from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from exceptions import ModuleProcessingError, module_exception_handler
from router import router


@pytest.mark.asyncio
async def test_health_route() -> None:
    app = FastAPI()
    app.state.settings = type("S", (), {"service_version": "1.0.0"})()
    app.include_router(router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_run_invalid_payload_returns_422() -> None:
    app = FastAPI()
    app.state.settings = type("S", (), {"service_version": "1.0.0"})()
    app.state.db_pool = object()
    app.state.vector_db_pool = object()
    app.state.llm_client = object()
    app.state.nlp_model = object()
    app.include_router(router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/run", json={"company_id": "not-uuid", "sample_posts": []})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_module_error_handler() -> None:
    app = FastAPI()
    app.add_exception_handler(ModuleProcessingError, module_exception_handler)

    @app.get("/boom")
    async def boom() -> None:
        raise ModuleProcessingError("code", "message", False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "code"
