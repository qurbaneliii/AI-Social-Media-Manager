from __future__ import annotations

from ai.agents.content_generator_agent import ContentGeneratorAgent
from ai.agents.quality_review_agent import QualityReviewAgent
from ai.memory import BrandMemory
from ai.persistence import AIPersistenceRepository, PersistenceAuditMetadata
from ai.schemas.content import ContentRequest, GeneratedContentPackage


class GenerateContentPackageWorkflow:
    def __init__(
        self,
        brand_memory: BrandMemory,
        content_generator: ContentGeneratorAgent,
        quality_reviewer: QualityReviewAgent,
        persistence_repository: AIPersistenceRepository | None = None,
        audit_metadata: PersistenceAuditMetadata | None = None,
    ) -> None:
        self.brand_memory = brand_memory
        self.content_generator = content_generator
        self.quality_reviewer = quality_reviewer
        self.persistence_repository = persistence_repository
        self.audit_metadata = audit_metadata

    async def run(self, request: ContentRequest) -> GeneratedContentPackage:
        brand_profile = await self.brand_memory.load_brand_profile(request.brand_profile)
        hydrated_request = request.model_copy(update={"brand_profile": brand_profile})
        package = await self.content_generator.generate(hydrated_request)
        review = await self.quality_reviewer.review(hydrated_request, package)
        reviewed_package = package.model_copy(update={"quality_scores": review})
        if self.persistence_repository is not None and self.audit_metadata is not None:
            audit_metadata = self.audit_metadata.model_copy(update={"quality_scores": review.model_dump(mode="json")})
            draft = await self.persistence_repository.save_content_draft(
                hydrated_request,
                reviewed_package,
                audit_metadata,
            )
            await self.persistence_repository.save_quality_review(
                draft_id=draft.get("draft_id"),
                brand_id=hydrated_request.brand_profile.brand_id,
                review=review,
                audit_metadata=audit_metadata,
            )
        return reviewed_package

