from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProductContext(BaseModel):
    product_name: str = "ARIA"
    product_role: str = "AI Social Media Manager and Brand Manager"
    default_workflow_mode: str = "approval_based"
    supported_capabilities: list[str] = Field(
        default_factory=lambda: [
            "strategy",
            "content_generation",
            "hashtag_recommendation",
            "visual_concept_generation",
            "calendar_planning",
            "community_management",
            "reporting",
            "competitor_analysis",
            "trend_research",
            "approval_workflow",
        ]
    )
    automation_boundaries: list[str] = Field(
        default_factory=lambda: [
            "no_auto_publish",
            "no_auto_reply",
            "no_real_platform_scheduling",
            "no_scraping_without_future_integration",
        ]
    )
    default_safety_rules: list[str] = Field(
        default_factory=lambda: [
            "AI outputs are drafts until reviewed by a human.",
            "Approval does not publish content.",
            "Calendar readiness does not schedule to real platforms.",
            "Community reply approval does not send a reply.",
            "Competitor and trend intelligence uses only provided data until future integrations exist.",
        ]
    )
    required_brand_inputs: list[str] = Field(
        default_factory=lambda: [
            "brand_name",
            "industry",
            "description",
            "products_or_services",
            "target_audience",
            "tone_of_voice",
            "brand_values",
            "platforms",
            "business_goals",
        ]
    )
    optional_manual_data_inputs: list[str] = Field(
        default_factory=lambda: [
            "competitor_examples",
            "trend_keywords",
            "analytics_metrics",
            "campaign_brief",
            "content_topic",
            "target_platform",
            "community_message_text",
            "reporting_date_range",
        ]
    )


class BrandProfile(BaseModel):
    brand_id: str
    brand_name: str
    industry: str
    description: str = ""
    products_or_services: list[str] = Field(default_factory=list)
    target_audience: list[str] = Field(default_factory=list)
    tone_of_voice: list[str] = Field(default_factory=list)
    brand_values: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    forbidden_words: list[str] = Field(default_factory=list)
    approved_claims: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    visual_style: dict[str, Any] = Field(default_factory=dict)
    business_goals: list[str] = Field(default_factory=list)
    language_preferences: list[str] = Field(default_factory=lambda: ["en"])


class BrandProfileValidationResult(BaseModel):
    brand_id: str
    completeness_score: int = Field(ge=0, le=100)
    is_complete: bool
    required_fields: list[str]
    missing_required_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    using_default_context: bool = False


class BrandProfileResponse(BaseModel):
    profile: BrandProfile
    validation: BrandProfileValidationResult
    product_context: ProductContext = Field(default_factory=ProductContext)
    persisted: bool = True


def validate_brand_profile_completeness(
    profile: BrandProfile,
    *,
    using_default_context: bool = False,
) -> BrandProfileValidationResult:
    required_fields = ProductContext().required_brand_inputs
    missing: list[str] = []
    for field_name in required_fields:
        value = getattr(profile, field_name)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field_name)

    warnings: list[str] = []
    if not profile.approved_claims:
        warnings.append("approved_claims is empty; AI outputs should avoid factual product claims.")
    if not profile.forbidden_words and not profile.forbidden_topics:
        warnings.append("No forbidden words or topics are configured.")
    if using_default_context:
        warnings.append("AI workflows are using default/mock brand context until a real BrandProfile is saved.")

    completeness_score = round(((len(required_fields) - len(missing)) / len(required_fields)) * 100)
    return BrandProfileValidationResult(
        brand_id=profile.brand_id,
        completeness_score=completeness_score,
        is_complete=len(missing) == 0,
        required_fields=required_fields,
        missing_required_fields=missing,
        warnings=warnings,
        using_default_context=using_default_context,
    )

