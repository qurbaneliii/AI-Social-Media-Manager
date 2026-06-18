from __future__ import annotations

from ai.agents.content_generator_agent import ContentGeneratorAgent
from ai.agents.quality_review_agent import QualityReviewAgent
from ai.memory import BrandMemory
from ai.schemas.content import ContentRequest, GeneratedContentPackage


class GenerateContentPackageWorkflow:
    def __init__(
        self,
        brand_memory: BrandMemory,
        content_generator: ContentGeneratorAgent,
        quality_reviewer: QualityReviewAgent,
    ) -> None:
        self.brand_memory = brand_memory
        self.content_generator = content_generator
        self.quality_reviewer = quality_reviewer

    async def run(self, request: ContentRequest) -> GeneratedContentPackage:
        brand_profile = await self.brand_memory.load_brand_profile(request.brand_profile)
        hydrated_request = request.model_copy(update={"brand_profile": brand_profile})
        package = await self.content_generator.generate(hydrated_request)
        review = await self.quality_reviewer.review(hydrated_request, package)
        return package.model_copy(update={"quality_scores": review})

