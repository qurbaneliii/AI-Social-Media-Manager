from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from ai.schemas.brand import BrandProfile
from api.dependencies import WorkspaceContext, get_product_repository, get_workspace_context


class RuntimeContractRepository:
    def __init__(self) -> None:
        self.posts: dict[str, dict] = {}
        self.calendar: dict[str, dict] = {}

    async def get_brand_profile(self, workspace_id: str, brand_id: str) -> dict:
        profile = BrandProfile(
            brand_id=brand_id,
            brand_name="Contract Brand",
            industry="software",
            products_or_services=["ARIA"],
            target_audience=["social teams"],
            tone_of_voice=["clear"],
            brand_values=["truthfulness"],
            platforms=["linkedin"],
            business_goals=["approval-ready content"],
        )
        return {"brand_profile_json": profile.model_dump(mode="json")}

    async def create_content(self, **values) -> str:
        post_id = str(uuid4())
        package = values["packages"][0]
        variant_id = str(uuid4())
        content_text = "\n\n".join(package[key] for key in ("hook", "caption", "cta") if package.get(key))
        self.posts[post_id] = {
            "draft_id": post_id,
            "generation_status": "generated",
            "content_package_json": package,
            "selected_variant_id": variant_id,
            "variants": [
                {
                    "variant_id": variant_id,
                    "platform": package["platform"],
                    "content_text": content_text,
                    "package": package,
                    "scores": package.get("quality_scores") or {},
                    "is_selected": True,
                }
            ],
        }
        return post_id

    async def get_content(self, workspace_id: str, post_id: str) -> dict | None:
        return self.posts.get(post_id)

    async def save_user_draft(self, **values) -> str:
        post_id = str(uuid4())
        self.posts[post_id] = {
            "draft_id": post_id,
            "generation_status": "draft",
            "selected_variant_id": None,
            "variants": [],
        }
        return post_id

    async def list_content(self, **values) -> tuple[list[dict], int]:
        rows = list(self.posts.values())
        return rows, len(rows)

    async def create_calendar_item(self, **values) -> dict | None:
        if values["content_draft_id"] not in self.posts:
            return None
        item_id = str(uuid4())
        row = {
            "calendar_item_id": item_id,
            "content_draft_id": values["content_draft_id"],
            "platform": values["platform"],
            "planned_at": values["planned_at"],
            "planning_state": "draft_plan",
            "approval_status": "draft",
        }
        self.calendar[item_id] = row
        return row

    async def list_calendar_items(self, **values) -> tuple[list[dict], int]:
        rows = list(self.calendar.values())
        return rows, len(rows)

    async def update_calendar_item(self, **values) -> dict | None:
        row = self.calendar.get(values["item_id"])
        if row:
            row["planning_state"] = values["planning_state"]
        return row


def test_render_entrypoint_exposes_frontend_required_public_routes() -> None:
    from main import app

    route_contract = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    expected = {
        ("POST", "/internal/ai/generate-content-package"),
        ("POST", "/internal/ai/content/refine"),
        ("POST", "/internal/ai/content-quality/review"),
        ("POST", "/internal/ai/hashtags/recommend"),
        ("POST", "/internal/ai/trends/research"),
        ("POST", "/v1/posts/generate"),
        ("GET", "/v1/posts/{post_id}"),
        ("POST", "/v1/posts/drafts"),
        ("GET", "/v1/companies/{company_id}/posts"),
        ("POST", "/v1/schedules"),
        ("GET", "/v1/schedules/{schedule_id}"),
        ("POST", "/v1/schedules/{schedule_id}/approve"),
    }

    assert expected.issubset(route_contract)


def test_public_post_and_schedule_contract_flow_works_without_preview_routes() -> None:
    from main import app

    repository = RuntimeContractRepository()
    app.dependency_overrides[get_product_repository] = lambda: repository
    app.dependency_overrides[get_workspace_context] = lambda: WorkspaceContext(
        workspace_id="workspace-1",
        workspace_name="Contract Workspace",
        brand_id="company-1",
        brand_name="Contract Brand",
        user_id="user-1",
        email="user@example.com",
        role="brand_manager",
    )
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
    assert schedule_response.json()["status"] == "draft_plan"
    assert schedule_response.json()["external_scheduling"] == "unavailable"
    schedule_id = schedule_response.json()["schedule_ids"][0]

    detail_response = client.get(f"/v1/schedules/{schedule_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["external_scheduling_status"] == "not_implemented"

    approve_response = client.post(f"/v1/schedules/{schedule_id}/approve", json={"company_id": "company-1"})
    assert approve_response.status_code == 200
    assert approve_response.json()["approved"] is True
    assert approve_response.json()["status"] == "approved_internal"
    assert approve_response.json()["external_scheduling"] == "unavailable"
    assert approve_response.json()["approved_by"] == "user-1"
    app.dependency_overrides.clear()


def test_legacy_ai_routes_are_not_part_of_render_entrypoint_contract() -> None:
    from main import app

    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/ai/generate-content" not in route_paths
    assert "/ai/generate-batch" not in route_paths
    assert "/ai/improve-content" not in route_paths
    assert "/ai/analyze-content" not in route_paths
    assert "/ai/suggest-hashtags" not in route_paths
    assert "/ai/suggest-topics" not in route_paths
