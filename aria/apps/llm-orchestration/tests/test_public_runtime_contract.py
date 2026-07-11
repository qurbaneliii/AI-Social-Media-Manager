from __future__ import annotations

from fastapi.testclient import TestClient


def test_render_entrypoint_exposes_frontend_required_public_routes() -> None:
    from main import app

    route_paths = {getattr(route, "path", "") for route in app.routes}
    expected = {
        "/internal/ai/generate-content-package",
        "/internal/ai/content/refine",
        "/internal/ai/content-quality/review",
        "/internal/ai/hashtags/recommend",
        "/internal/ai/trends/research",
        "/v1/posts/generate",
        "/v1/posts/{post_id}",
        "/v1/posts/drafts",
        "/v1/companies/{company_id}/posts",
        "/v1/schedules",
        "/v1/schedules/{schedule_id}",
        "/v1/schedules/{schedule_id}/approve",
    }

    assert expected.issubset(route_paths)


def test_public_post_and_schedule_contract_flow_works_without_preview_routes() -> None:
    from main import PUBLIC_POST_STORE, PUBLIC_SCHEDULE_STORE, app

    PUBLIC_POST_STORE.clear()
    PUBLIC_SCHEDULE_STORE.clear()
    client = TestClient(app)

    generate_response = client.post(
        "/v1/posts/generate",
        json={
            "company_id": "company-1",
            "post_intent": "educate",
            "core_message": "Explain how approval keeps AI-generated social posts safer.",
            "target_platforms": ["linkedin"],
            "campaign_tag": "runtime-contract",
            "manual_keywords": ["approval", "brand safety"],
            "urgency_level": "immediate",
        },
    )
    assert generate_response.status_code == 200
    generated = generate_response.json()
    assert generated["status"] == "generated"

    post_response = client.get(f"/v1/posts/{generated['post_id']}")
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["generated_package_json"]["variants"][0]["text"]

    draft_response = client.post(
        "/v1/posts/drafts",
        json={
            "company_id": "company-1",
            "platform": "linkedin",
            "content": "A saved draft from the runtime contract flow.",
            "intent": "educate",
        },
    )
    assert draft_response.status_code == 200
    assert draft_response.json()["status"] == "draft"

    list_response = client.get("/v1/companies/company-1/posts?limit=10&offset=0")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 2

    schedule_response = client.post(
        "/v1/schedules",
        json={
            "post_id": generated["post_id"],
            "company_id": "company-1",
            "targets": [{"platform": "linkedin", "run_at_utc": "2026-07-12T09:00:00Z"}],
            "approval_mode": "human",
        },
    )
    assert schedule_response.status_code == 200
    schedule_id = schedule_response.json()["schedule_ids"][0]

    detail_response = client.get(f"/v1/schedules/{schedule_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["external_scheduling_status"] == "not_implemented"

    approve_response = client.post(f"/v1/schedules/{schedule_id}/approve", json={"company_id": "company-1"})
    assert approve_response.status_code == 200
    assert approve_response.json()["approved"] is True


def test_legacy_ai_routes_are_not_part_of_render_entrypoint_contract() -> None:
    from main import app

    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/ai/generate-content" not in route_paths
    assert "/ai/generate-batch" not in route_paths
    assert "/ai/improve-content" not in route_paths
    assert "/ai/analyze-content" not in route_paths
    assert "/ai/suggest-hashtags" not in route_paths
    assert "/ai/suggest-topics" not in route_paths
