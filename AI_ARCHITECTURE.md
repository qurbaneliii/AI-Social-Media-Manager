# AI Architecture

## Overview

ARIA's AI layer is an approval-based orchestration system, not a monolithic chatbot. The LLM orchestration service owns prompt assembly, model access, structured output validation, specialist agents, quality review, and future model/provider routing.

Phase 1 and Phase 2 live in `aria/apps/llm-orchestration/app/ai`.

## Module Responsibilities

- `llm/`: reads environment variables, chooses mock or OpenAI mode, sends structured requests, retries transient failures, validates responses, and avoids logging secrets.
- `prompts/`: central prompt registry with versioned brand, platform, content-generation, quality-review, and specialist-agent prompts.
- `schemas/`: Pydantic models for all major AI inputs/outputs.
- `memory/`: `BrandMemory` facade for schema-first brand profile access. It can later read from PostgreSQL and pgvector.
- `agents/`: reusable agent classes. Phase 2 adds the specialist agent layer behind `AIOrchestrator`.
- `workflows/`: end-to-end use-case composition. Phase 1 includes `GenerateContentPackageWorkflow`; Phase 2 keeps specialist orchestration thin and schema-first.
- `evaluation/`: quality score aggregation and approval validators.

## Data Flow

1. Client sends `ContentRequest` to `/internal/ai/generate-content-package`.
2. `AIOrchestrator` loads the brand profile through `BrandMemory`.
3. `ContentGeneratorAgent` builds prompts through `PromptRegistry`.
4. `LLMClient` uses mock mode when `AI_MOCK_MODE=true` or no valid `OPENAI_API_KEY` exists.
5. The generated JSON is validated as `GeneratedContentPackage`.
6. `QualityReviewAgent` assigns `AIQualityReview` scores and approval status.
7. The response is returned as a structured, human-reviewable content package.

## Agent List

- `BrandStrategyAgent`: positioning suggestions, content pillars, campaign angles, audience hypotheses, and strategic recommendations.
- `CompetitorAnalysisAgent`: analyzes only provided competitor/post data for engagement patterns, hooks, themes, hashtags, tone, posting patterns, and content gaps.
- `TrendResearchAgent`: analyzes only provided trends/keywords/topics for relevant topics, hashtags, formats, and opportunities.
- `ContentGeneratorAgent`: hooks, captions, CTAs, hashtags, visual briefs, and rationale. Skeleton working path in Phase 1.
- `HashtagAgent`: grouped niche, broad, branded, campaign, location, and trend-based hashtag recommendations with risk notes.
- `VisualConceptAgent`: visual briefs, carousel concepts, short-form video concepts, image-generation prompts, design direction, mood, scene, layout, and constraints. It does not generate images.
- `CalendarPlanningAgent`: weekly/monthly draft calendars balancing pillars, objectives, platform mix, frequency, content type, and posting time.
- `CommunityManagementAgent`: sentiment, intent, urgency, toxicity, complaint, buying, FAQ, crisis classification, and brand-safe reply drafts. It never auto-replies.
- `ReportingAgent`: converts provided analytics into readable insights, recommended changes, and next experiments.
- `QualityReviewAgent`: brand consistency, platform fit, clarity, CTA, originality, risk, and approval review. Skeleton working path in Phase 1.

## Orchestrator Routing Map

- `generate_content_package` -> `ContentGeneratorAgent` plus `QualityReviewAgent`
- `create_brand_strategy` -> `BrandStrategyAgent`
- `analyze_competitors` -> `CompetitorAnalysisAgent`
- `research_trends` -> `TrendResearchAgent`
- `recommend_hashtags` -> `HashtagAgent`
- `generate_visual_concept` -> `VisualConceptAgent`
- `create_content_calendar` -> `CalendarPlanningAgent`
- `analyze_community_message` -> `CommunityManagementAgent`
- `generate_report_insights` -> `ReportingAgent`
- `review_content_quality` -> `QualityReviewAgent`

## Schema List

- `BrandProfile`
- `PlatformContext`
- `ContentRequest`
- `GeneratedContentPackage`
- `BrandStrategyRequest`
- `BrandStrategyPlan`
- `CompetitorPostData`
- `CompetitorAnalysisRequest`
- `CompetitorInsightReport`
- `TrendInputData`
- `TrendResearchRequest`
- `TrendInsightReport`
- `HashtagRecommendationRequest`
- `HashtagRecommendation`
- `VisualConceptRequest`
- `VisualConceptPackage`
- `CalendarPlanningRequest`
- `CommunityMessageAnalysis`
- `CommunityManagementRequest`
- `ContentCalendarItem`
- `ContentCalendarPlan`
- `ReportingInsightRequest`
- `ReportingInsightReport`
- `ReportInsights`
- `AIQualityReview`
- `AgentExecutionResult`

## OpenAI Usage

The only Phase 1 provider path is `LLMClient`. It reads:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `AI_MOCK_MODE`
- `AI_TEMPERATURE`
- `AI_MAX_RETRIES`
- `AI_REQUEST_TIMEOUT_SECONDS`

No secrets are hardcoded. If OpenAI is configured and mock mode is false, the client calls OpenAI's chat completions endpoint with JSON-object response formatting and validates the result through Pydantic.

## Mock Mode

Mock mode is enabled by default in `.env.example`. It returns deterministic structured content, strategy, competitor, trend, hashtag, visual, calendar, community, reporting, and quality-review objects through each agent's `mock_factory`. This keeps local development usable without API keys and keeps publishing/replying disabled.

Community outputs always set `auto_reply_allowed=false`. Calendar outputs remain drafts with `approval_required=true`. Visual concepts are briefs only and do not generate images. Competitor and trend agents only work from provided input data and never scrape or browse.

## Future Integration Points

- Persist `BrandProfile`, generated packages, calendars, and quality reviews in the existing backend data layer.
- Connect competitor, trend, community, and reporting agents to approved internal datasets after ingestion is implemented.
- Add API routes around each orchestrator method once backend contracts are finalized.
- Add frontend approval queues for draft content, community replies, calendars, and strategy recommendations.
- Add observability for prompt version, model, cost, latency, approval decisions, and quality scores.

## Adding A New Agent

1. Add or reuse Pydantic input/output schemas in `ai/schemas`.
2. Add a versioned prompt in `ai/prompts`.
3. Create an agent class extending `BaseAgent`.
4. Call `LLMClient.generate_structured` with a schema and mock factory.
5. Compose the agent inside `AIOrchestrator` or a workflow.
6. Add tests for schema validation, prompt loading, and mock-mode execution.

## Roadmap

- Phase 2: implemented specialist agent skeletons with mock-mode outputs.
- Phase 3: connect specialist-agent routes to backend APIs, persistence, approval queues, and saved brand memory.
- Phase 4: implement approved internal data ingestion for competitor, trend, reporting, and community workflows.
- Phase 5: implement multi-platform content workflows and deeper calendar operations.
- Phase 6: persist generated packages, audit logs, and approval states.
- Phase 7: wire frontend approval UX to the orchestration endpoint.
- Phase 8: add eval datasets, cost tracking, prompt version metrics, observability, and production guardrails.
