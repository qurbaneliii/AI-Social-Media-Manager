from __future__ import annotations

from ai.schemas.content import ContentRequest, GeneratedContentPackage

from .base import BaseAgent


class ContentGeneratorAgent(BaseAgent):
    async def generate(self, request: ContentRequest) -> GeneratedContentPackage:
        messages = self.prompt_registry.build_content_generation_messages(request)
        return await self.llm_client.generate_structured(
            messages,
            GeneratedContentPackage,
            mock_factory=lambda: self._mock_content_package(request),
        )

    def _mock_content_package(self, request: ContentRequest) -> dict:
        brand = request.brand_profile
        platform = request.platform_context.platform
        hashtag_limit = request.platform_context.hashtag_limit or 5
        seed_topic = request.topic.strip() or request.campaign_objective
        return {
            "platform": platform,
            "content_type": request.platform_context.content_type,
            "hook": f"{seed_topic}: a practical angle for {brand.brand_name}",
            "caption": (
                f"{brand.brand_name} helps {', '.join(brand.target_audience) or 'its audience'} "
                f"move toward {request.campaign_objective}. {request.extra_context.get('note', '')}".strip()
            ),
            "cta": "Review this draft, then choose the strongest angle for approval.",
            "hashtags": [f"#{platform}", "#brandstrategy", "#socialmedia"][:hashtag_limit],
            "visual_brief": {
                "direction": "Use brand-consistent visuals with a clear focal point and readable overlay text.",
                "style": brand.visual_style,
            },
            "video_script": None,
            "carousel_structure": [],
            "posting_recommendation": {
                "approval_required": True,
                "suggested_window": "Use audience timing service in Phase 2.",
            },
            "rationale": "Mock mode generated a safe, approval-based content package from schema inputs.",
            "risks": ["Mock output requires human review before publishing."],
        }

