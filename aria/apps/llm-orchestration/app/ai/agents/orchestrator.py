from __future__ import annotations

from typing import Any

from ai.agents.brand_strategy_agent import BrandStrategyAgent
from ai.agents.calendar_planning_agent import CalendarPlanningAgent
from ai.agents.community_management_agent import CommunityManagementAgent
from ai.agents.competitor_analysis_agent import CompetitorAnalysisAgent
from ai.agents.content_generator_agent import ContentGeneratorAgent
from ai.agents.hashtag_agent import HashtagAgent
from ai.agents.quality_review_agent import QualityReviewAgent
from ai.agents.reporting_agent import ReportingAgent
from ai.agents.trend_research_agent import TrendResearchAgent
from ai.agents.visual_concept_agent import VisualConceptAgent
from ai.llm import LLMClient
from ai.memory import BrandMemory
from ai.prompts import PromptRegistry
from ai.schemas.analytics import ReportingInsightReport, ReportingInsightRequest
from ai.schemas.calendar import CalendarPlanningRequest, ContentCalendarPlan
from ai.schemas.community import CommunityManagementRequest, CommunityMessageAnalysis
from ai.schemas.competitor import CompetitorAnalysisRequest, CompetitorInsightReport
from ai.schemas.content import ContentRequest, GeneratedContentPackage
from ai.schemas.evaluation import AIQualityReview
from ai.schemas.hashtag import HashtagRecommendation, HashtagRecommendationRequest
from ai.schemas.strategy import BrandStrategyPlan, BrandStrategyRequest
from ai.schemas.trend import TrendInsightReport, TrendResearchRequest
from ai.schemas.visual import VisualConceptPackage, VisualConceptRequest
from ai.workflows import GenerateContentPackageWorkflow


class AIOrchestrator:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        brand_memory: BrandMemory | None = None,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.brand_memory = brand_memory or BrandMemory()
        self.brand_strategy = BrandStrategyAgent(self.llm_client, self.prompt_registry)
        self.competitor_analysis = CompetitorAnalysisAgent(self.llm_client, self.prompt_registry)
        self.content_generator = ContentGeneratorAgent(self.llm_client, self.prompt_registry)
        self.trend_research = TrendResearchAgent(self.llm_client, self.prompt_registry)
        self.hashtag_agent = HashtagAgent(self.llm_client, self.prompt_registry)
        self.visual_concept = VisualConceptAgent(self.llm_client, self.prompt_registry)
        self.calendar_planning = CalendarPlanningAgent(self.llm_client, self.prompt_registry)
        self.community_management = CommunityManagementAgent(self.llm_client, self.prompt_registry)
        self.reporting = ReportingAgent(self.llm_client, self.prompt_registry)
        self.quality_reviewer = QualityReviewAgent(self.llm_client, self.prompt_registry)

    async def generate_content_package(self, request: ContentRequest) -> GeneratedContentPackage:
        workflow = GenerateContentPackageWorkflow(
            self.brand_memory,
            self.content_generator,
            self.quality_reviewer,
        )
        return await workflow.run(request)

    async def create_brand_strategy(self, request: BrandStrategyRequest) -> BrandStrategyPlan:
        return await self.brand_strategy.create_strategy(request)

    async def analyze_competitors(self, request: CompetitorAnalysisRequest) -> CompetitorInsightReport:
        return await self.competitor_analysis.analyze(request)

    async def research_trends(self, request: TrendResearchRequest) -> TrendInsightReport:
        return await self.trend_research.research(request)

    async def recommend_hashtags(self, request: HashtagRecommendationRequest) -> HashtagRecommendation:
        return await self.hashtag_agent.recommend(request)

    async def generate_visual_concept(self, request: VisualConceptRequest) -> VisualConceptPackage:
        return await self.visual_concept.generate(request)

    async def create_content_calendar(self, request: CalendarPlanningRequest) -> ContentCalendarPlan:
        return await self.calendar_planning.create_calendar(request)

    async def analyze_community_message(self, request: CommunityManagementRequest) -> CommunityMessageAnalysis:
        return await self.community_management.analyze(request)

    async def generate_report_insights(self, request: ReportingInsightRequest) -> ReportingInsightReport:
        return await self.reporting.generate_insights(request)

    async def review_content_quality(
        self,
        request: ContentRequest | dict[str, Any],
        package: GeneratedContentPackage | dict[str, Any],
    ) -> AIQualityReview:
        if isinstance(request, ContentRequest) and isinstance(package, GeneratedContentPackage):
            return await self.quality_reviewer.review(request, package)
        return await self.quality_reviewer.review_structured_output({"request": request, "output": package})
