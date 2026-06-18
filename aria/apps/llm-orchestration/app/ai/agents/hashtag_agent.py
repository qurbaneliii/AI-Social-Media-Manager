from __future__ import annotations

from ai.schemas.hashtag import HashtagRecommendation, HashtagRecommendationRequest

from .base import BaseAgent


class HashtagAgent(BaseAgent):
    async def recommend(self, request: HashtagRecommendationRequest) -> HashtagRecommendation:
        messages = self.prompt_registry.build_agent_messages(
            "hashtag_recommendation",
            request.model_dump(mode="json"),
        )
        return await self.llm_client.generate_structured(
            messages,
            HashtagRecommendation,
            mock_factory=lambda: self._mock_recommendation(request),
        )

    def _mock_recommendation(self, request: HashtagRecommendationRequest) -> dict:
        brand_tag = request.brand_profile.brand_name.replace(" ", "")
        campaign_tag = (request.campaign_name or request.topic).replace(" ", "")
        location_tags = [request.location.replace(" ", "")] if request.location else []
        return {
            "niche_hashtags": [request.topic.replace(" ", ""), request.brand_profile.industry.replace(" ", "")],
            "broad_hashtags": ["SocialMedia", "BrandStrategy"],
            "branded_hashtags": [brand_tag],
            "campaign_hashtags": [campaign_tag],
            "location_hashtags": location_tags,
            "trend_based_hashtags": [keyword.replace(" ", "") for keyword in request.trend_keywords[:3]],
            "risk_notes": ["Review hashtags for relevance and local compliance before approval."],
            "rationale": "Mock recommendation keeps hashtags grouped and avoids stuffing.",
        }

