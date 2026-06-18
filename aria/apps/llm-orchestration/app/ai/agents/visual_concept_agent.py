from __future__ import annotations

from ai.schemas.visual import VisualConceptPackage, VisualConceptRequest

from .base import BaseAgent


class VisualConceptAgent(BaseAgent):
    async def generate(self, request: VisualConceptRequest) -> VisualConceptPackage:
        messages = self.prompt_registry.build_agent_messages(
            "visual_concept",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            VisualConceptPackage,
            mock_factory=lambda: self._mock_package(request),
        )

    def _mock_package(self, request: VisualConceptRequest) -> dict:
        brand = request.brand_profile
        return {
            "visual_brief": f"Create a {request.platform_context.content_type} concept for {request.topic}.",
            "carousel_concepts": [
                {
                    "slides": 5,
                    "structure": ["problem", "insight", "proof", "workflow", "approval CTA"],
                }
            ],
            "short_form_video_concepts": [
                {
                    "duration_seconds": 30,
                    "beats": ["hook", "quick demo", "human approval moment", "CTA"],
                }
            ],
            "image_generation_prompts": [
                f"Brand-safe {brand.industry} workspace visual about {request.topic}; no logos unless provided."
            ],
            "design_direction": {
                "style": brand.visual_style,
                "platform": request.platform_context.platform,
            },
            "mood": ["confident", "clear", "useful"],
            "scene": "A clean working environment focused on the campaign idea.",
            "layout": "Strong focal point, minimal overlay text, accessible contrast.",
            "creative_constraints": request.creative_constraints,
            "risk_notes": ["This package is a brief only and does not generate images."],
        }

