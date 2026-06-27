from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from ai.prompts import PromptRegistry
from ai.schemas.brand import BrandProfile, ProductContext, validate_brand_profile_completeness
from ai.schemas.content import ContentRequest, PlatformContext


def _brand_profile(**overrides: Any) -> BrandProfile:
    data: dict[str, Any] = {
        "brand_id": "brand-1",
        "brand_name": "ARIA Labs",
        "industry": "Marketing software",
        "description": "Approval-based AI social media management.",
        "products_or_services": ["AI content workspace"],
        "target_audience": ["founders", "marketing teams"],
        "tone_of_voice": ["clear", "strategic"],
        "brand_values": ["human control", "useful automation"],
        "approved_claims": ["Helps teams review AI-generated social drafts."],
        "forbidden_words": ["guaranteed"],
        "forbidden_topics": ["medical advice"],
        "competitors": ["Manual spreadsheets"],
        "platforms": ["linkedin"],
        "visual_style": {"palette": ["teal", "slate"]},
        "business_goals": ["increase content quality"],
        "language_preferences": ["en"],
    }
    data.update(overrides)
    return BrandProfile(**data)


class BrandRepository:
    def __init__(self, profile: BrandProfile | None = None) -> None:
        self.profile = profile
        self.saved: BrandProfile | None = None

    async def load_brand_profile(self, brand_id: str) -> BrandProfile | None:
        if self.profile and self.profile.brand_id == brand_id:
            return self.profile
        return None

    async def save_brand_profile(self, profile: BrandProfile) -> dict[str, Any]:
        self.saved = profile
        self.profile = profile
        return {"brand_id": profile.brand_id}


def test_product_context_defines_social_manager_boundaries() -> None:
    context = ProductContext()

    assert context.product_name == "ARIA"
    assert context.default_workflow_mode == "approval_based"
    assert "content_generation" in context.supported_capabilities
    assert "approval_workflow" in context.supported_capabilities
    assert "no_auto_publish" in context.automation_boundaries
    assert "no_auto_reply" in context.automation_boundaries
    assert "no_real_platform_scheduling" in context.automation_boundaries


def test_brand_profile_validation_reports_missing_fields() -> None:
    profile = _brand_profile(description="", products_or_services=[], platforms=[])

    validation = validate_brand_profile_completeness(profile, using_default_context=True)

    assert validation.is_complete is False
    assert validation.using_default_context is True
    assert "description" in validation.missing_required_fields
    assert "products_or_services" in validation.missing_required_fields
    assert "platforms" in validation.missing_required_fields
    assert validation.completeness_score < 100


def test_brand_profile_routes_return_safe_schema() -> None:
    from main import app, get_persistence_repository

    repo = BrandRepository(_brand_profile())
    app.dependency_overrides[get_persistence_repository] = lambda: repo
    try:
        client = TestClient(app)
        get_response = client.get("/internal/ai/brand-profile/brand-1")
        upsert_response = client.post(
            "/internal/ai/brand-profile",
            json={"profile": _brand_profile(brand_name="ARIA Studio").model_dump(mode="json")},
        )
        validate_response = client.post(
            "/internal/ai/brand-profile/validate",
            json={"profile": _brand_profile(description="").model_dump(mode="json"), "using_default_context": True},
        )

        assert get_response.status_code == 200
        assert get_response.json()["profile"]["brand_id"] == "brand-1"
        assert "brand_profile_json" not in get_response.json()
        assert upsert_response.status_code == 200
        assert upsert_response.json()["profile"]["brand_name"] == "ARIA Studio"
        assert repo.saved is not None
        assert validate_response.status_code == 200
        assert "description" in validate_response.json()["missing_required_fields"]
    finally:
        app.dependency_overrides.clear()


def test_brand_profile_routes_handle_missing_and_unconfigured() -> None:
    from main import app, get_persistence_repository

    app.dependency_overrides[get_persistence_repository] = lambda: BrandRepository(None)
    try:
        client = TestClient(app)
        missing = client.get("/internal/ai/brand-profile/missing-brand")
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()

    client = TestClient(app)
    unconfigured = client.get("/internal/ai/brand-profile/brand-1")
    assert unconfigured.status_code == 503


def test_ai_workspace_routes_are_registered() -> None:
    from main import app

    route_paths = {getattr(route, "path", "") for route in app.routes}
    expected = {
        "/internal/ai/workspace-context",
        "/internal/ai/brand-profile/{brand_id}",
        "/internal/ai/brand-profile",
        "/internal/ai/brand-profile/validate",
        "/internal/ai/generate-content-package",
        "/internal/ai/brand-strategy",
        "/internal/ai/competitors/analyze",
        "/internal/ai/trends/research",
        "/internal/ai/hashtags/recommend",
        "/internal/ai/visual-concept",
        "/internal/ai/content-calendar",
        "/internal/ai/community/analyze",
        "/internal/ai/reports/insights",
        "/internal/ai/content-quality/review",
    }

    assert expected.issubset(route_paths)


def test_prompt_registry_includes_product_context_in_agent_payloads() -> None:
    registry = PromptRegistry()
    request = ContentRequest(
        brand_profile=_brand_profile(),
        platform_context=PlatformContext(platform="linkedin", content_type="post", objective="educate"),
        campaign_objective="build trust",
        topic="approval-based AI workspace",
        content_pillar="education",
    )

    messages = registry.build_content_generation_messages(request)
    user_message = messages[-1].content

    assert "product_context" in user_message
    assert "AI Social Media Manager and Brand Manager" in user_message
    assert "no_auto_publish" in user_message
