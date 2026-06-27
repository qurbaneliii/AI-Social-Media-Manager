# AI Architecture

## Overview

ARIA's AI layer is an approval-based orchestration system, not a monolithic chatbot. The LLM orchestration service owns prompt assembly, model access, structured output validation, specialist agents, quality review, and future model/provider routing.

Phase 1 and Phase 2 live in `aria/apps/llm-orchestration/app/ai`.

## Module Responsibilities

- `llm/`: reads environment variables, chooses mock or OpenAI mode, sends structured requests, retries transient failures, validates responses, emits token/cost metadata hooks, and avoids logging secrets.
- `prompts/`: central prompt registry with versioned brand, platform, content-generation, quality-review, and specialist-agent prompts.
- `schemas/`: Pydantic models for all major AI inputs/outputs.
- `schemas.brand.ProductContext`: system-known ARIA product/workspace context, supported capabilities, automation boundaries, and Brand Brain required inputs.
- `memory/`: `BrandMemory` facade for schema-first brand profile access. It can later read from PostgreSQL and pgvector.
- `agents/`: reusable agent classes. Phase 2 adds the specialist agent layer behind `AIOrchestrator`.
- `workflows/`: end-to-end use-case composition. Phase 1 includes `GenerateContentPackageWorkflow`; Phase 2 keeps specialist orchestration thin and schema-first.
- `evaluation/`: quality score aggregation and approval validators.

## Data Flow

1. Client sends `ContentRequest` to `/internal/ai/generate-content-package`.
2. The LLM orchestration service creates an async database pool from `DATABASE_URL` during lifespan startup when the variable is configured.
3. `get_ai_orchestrator` injects `AIPersistenceRepository` when a runtime DB pool exists.
4. `AIOrchestrator` loads the brand profile through `BrandMemory`.
5. If persistence is enabled and mock/local bootstrap is not allowed, missing brand profiles raise a clear not-found error instead of silently falling back.
6. `ContentGeneratorAgent` builds prompts through `PromptRegistry`.
7. `LLMClient` uses mock mode when `AI_MOCK_MODE=true` or no valid `OPENAI_API_KEY` exists.
8. The generated JSON is validated as `GeneratedContentPackage`.
9. `QualityReviewAgent` assigns `AIQualityReview` scores and approval status.
10. If persistence is enabled, the generated package is stored as a draft and the quality review is stored with prompt/model/mock-mode audit metadata.
11. The response is returned as a structured, human-reviewable content package. It is not published.

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

No secrets are hardcoded. If OpenAI is configured and mock mode is false, the client calls OpenAI's chat completions endpoint with JSON-object response formatting, appends the target Pydantic JSON schema as an output instruction, and validates the result through Pydantic.

`LLMClient` accepts an optional `metadata_hook`. The hook receives `LLMMetadata` with provider, model, mock mode, token usage when OpenAI returns it, raw response id when available, schema name, and a future cost-estimation slot. The hook must not receive API keys or full prompt/user content.

`AI_MAX_RETRIES` controls retry behavior for real OpenAI calls. The value represents retries after the first attempt, so `AI_MAX_RETRIES=0` makes one request and `AI_MAX_RETRIES=2` allows three total attempts. Mock mode does not call the network and emits zero-cost metadata.

## Mock Mode

Mock mode is enabled by default in `.env.example`. It returns deterministic structured content, strategy, competitor, trend, hashtag, visual, calendar, community, reporting, and quality-review objects through each agent's `mock_factory`. This keeps local development usable without API keys and keeps publishing/replying disabled. Mock calls emit zero-cost metadata through the same hook used by real calls.

Community outputs always set `auto_reply_allowed=false`. Calendar outputs remain drafts with `approval_required=true`. Visual concepts are briefs only and do not generate images. Competitor and trend agents only work from provided input data and never scrape or browse. When a database repository is attached, mock/local mode may bootstrap the incoming schema-first `BrandProfile`; real mode requires a stored profile.

## Phase 3 Persistence

Phase 3 stores backend AI artifacts without enabling publishing, scraping, frontend approval UI, or automatic replies.

- `ai_brand_memory`: schema-first stored `BrandProfile` JSON by `brand_id`.
- `ai_content_drafts`: generated content packages as drafts with approval status, quality scores, prompt version, model, mock mode, and audit metadata.
- `ai_quality_reviews`: review scores, approval status, improvement notes, model, mock mode, and audit metadata.
- `ai_calendar_draft_items`: draft calendar items with approval-required defaults and audit metadata.

The migration is `aria/db/migrations/007_ai_memory_foundation.sql` and follows the existing filename-sorted `db.migrate` runner.

## Phase 4 Approval Lifecycle

Phase 4 adds backend-only approval lifecycle contracts for AI-generated drafts. The approval layer lives under `aria/apps/llm-orchestration/app/ai/approval` and is intentionally separated from social platform integrations.

- `schemas.py`: approval statuses, actions, decisions, audit events, and draft record DTOs.
- `transitions.py`: explicit allowed state transitions for content drafts, calendar draft items, community reply drafts, and report drafts.
- `service.py`: validates transitions, updates persistence, writes audit events, and returns schema-first results.
- `errors.py`: stable missing-record and invalid-transition errors for API handlers.

Runtime flow:

1. Internal clients call `/internal/ai/approval/...` with an approval decision or action request.
2. FastAPI builds `ApprovalService` from the configured `AIPersistenceRepository`.
3. The service loads the current draft record, validates the transition, updates the draft status, writes `ai_approval_audit_events`, and returns an `ApprovalResult`.
4. Invalid transitions return `409`; missing records return `404`.

Phase 4 lifecycle states are internal-only. `approved` does not publish content, `ready_for_scheduling` does not schedule to a platform, and approved community reply drafts are never sent automatically. Community reply draft storage enforces `auto_reply_allowed=false`.

The migration is `aria/db/migrations/008_ai_approval_lifecycle.sql`. Live Postgres verification is still pending because Phase 3.5 local database authentication failed.

## Phase 5 Approval Queues And Live DB Verification

Phase 5 stabilizes backend read contracts for future frontend approval queues and verifies the AI persistence flow against a real local Postgres database where possible.

Queue DTOs live in `aria/apps/llm-orchestration/app/ai/approval/queue.py`:

- `ContentDraftQueueItem`
- `CalendarDraftQueueItem`
- `CommunityReplyQueueItem`
- `ReportDraftQueueItem`
- `ApprovalQueueResponse`
- type-specific queue responses

Queue routes:

- `GET /internal/ai/approval/queue`
- `GET /internal/ai/approval/queue/content`
- `GET /internal/ai/approval/queue/calendar`
- `GET /internal/ai/approval/queue/community`
- `GET /internal/ai/approval/queue/reports`

Legacy draft list routes remain available, but now return sanitized DTOs instead of raw database rows:

- `GET /internal/ai/drafts/content`
- `GET /internal/ai/drafts/calendar`
- `GET /internal/ai/drafts/community`

The DTO layer exposes preview fields and summarized risk/quality metadata. It does not expose raw JSONB blobs such as `content_package_json`, `quality_scores_json`, `calendar_item_json`, `insight_payload_json`, or `metadata_json`.

Live database verification notes:

- The existing local server on `localhost:5432` rejects the expected credentials.
- Docker is unavailable, so the intended `aria/docker-compose.yml` pgvector stack could not be started.
- A temporary isolated Postgres database on `localhost:5433` verified migrations `007` and `008` directly and passed a real asyncpg persistence/approval flow.
- The full repo migration runner remains unverified in this environment because plain Postgres lacks the required `vector` extension from migration `001`.

Phase 5 does not add frontend UI, scraping, publishing, automatic replies, platform scheduling, or social platform API calls.

## Running Tests And Mock Mode

From `aria/apps/llm-orchestration`, install the Python test dependencies for the service environment, then run:

```bash
python -m pytest tests
```

For local mock mode, set:

```bash
AI_MOCK_MODE=true
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.4
AI_MAX_RETRIES=2
```

Then call the service endpoint:

```text
POST /internal/ai/generate-content-package
```

The endpoint returns a structured `GeneratedContentPackage` with quality scores and human-review status. It does not publish content or auto-reply to community messages.

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
- Phase 4: implement backend approval lifecycle, audit events, draft listing contracts, and safe community reply draft persistence.
- Phase 5: implemented live database verification path, read DTO hardening, and frontend-ready approval queue contracts.
- Phase 6: implemented frontend approval queues backed by the Phase 5 DTO routes, with lifecycle actions and audit history. Full pgvector migration-runner verification remains pending.
- Phase 7: implemented safe draft-detail DTOs, request-changes review context, approval audit timelines, frontend detail review UX, and deployment-facing API/CORS/env checks. Full pgvector migration-runner verification remains pending.
- Phase 8: implemented product AI workspace context, Brand Brain get/upsert/validate contracts, typed frontend orchestration clients, and dashboard modules for AI Workspace, Brand Brain, Content Studio, Strategy, Trends, Competitors, AI Analyst, Calendar AI, Community AI, Reports AI, and Approval Queue.
- Phase 9: add eval datasets, cost tracking, prompt version metrics, observability, production auth, and migration of legacy direct-provider frontend generator routes.

## Phase 6 Frontend Integration - 2026-06-19

The primary frontend approval workflow is now available under `/dashboard/approval`, with focused content, calendar, community, and report queue routes.

The dashboard calls only Phase 5's typed internal approval contracts:

- Queue DTO routes under `/internal/ai/approval/queue...`.
- Approval decision/action routes under `/internal/ai/approval/...`.
- Audit history under `/internal/ai/approval/audit/{object_type}/{object_id}`.

The frontend deliberately consumes preview and summary DTO fields only. It does not use persistence-level JSONB columns.

Safety remains unchanged:

- No frontend publishing, scheduling, scraping, social platform calls, or automatic replies were added.
- Approval is an internal lifecycle action only.
- `ready_for_scheduling` is not a real-platform schedule.
- Community reply drafts are never auto-sent.

Legacy direct-provider frontend helpers remain available for existing generator routes, but `app/api/ai/_lib.ts` and `lib/openai.ts` are marked deprecated for new approval workflow work. New approval UI code uses the centralized LLM orchestration service instead.

## Phase 7 Detail Review Contracts - 2026-06-27

Phase 7 extends the approval workflow from queue-level review into safe detail review without exposing persistence internals.

Backend detail DTOs live in `aria/apps/llm-orchestration/app/ai/approval/queue.py`:

- `ContentDraftDetail`
- `CalendarDraftDetail`
- `CommunityReplyDraftDetail`
- `ReportDraftDetail`
- `ApprovalAuditTimeline`

Detail routes:

- `GET /internal/ai/approval/detail/content/{draft_id}`
- `GET /internal/ai/approval/detail/calendar/{item_id}`
- `GET /internal/ai/approval/detail/community/{reply_draft_id}`
- `GET /internal/ai/approval/detail/reports/{report_id}`
- `GET /internal/ai/approval/detail/{object_type}/{object_id}`

The detail DTOs parse internal JSONB columns inside the backend and return curated review fields only. They include latest audit events, latest requested changes, and latest review reason where available. The frontend never receives raw fields such as `content_package_json`, `quality_scores_json`, `calendar_item_json`, `insight_payload_json`, `audit_metadata_json`, or `metadata_json`.

The frontend approval dashboard now opens typed detail records, shows audit timeline and request-changes history, validates request-changes reason plus change items, and keeps the existing safety model visible: approval does not publish, calendar readiness does not schedule, and community reply approval does not send replies.

Deployment-facing behavior:

- `NEXT_PUBLIC_AI_ORCHESTRATION_URL` can point the approval client at the LLM orchestration service.
- The approval client falls back to existing frontend API base URL variables when the dedicated variable is absent.
- The LLM orchestration service reads `CORS_ORIGINS` and defaults to local frontend origins for development.
- Reviewer identity remains explicit placeholder request metadata until a production auth system is wired through the internal approval routes.

## Phase 8 Product AI Workspace - 2026-06-27

Phase 8 expands ARIA from approval dashboard coverage into a broader AI Social Media Manager and Brand Manager workspace while preserving approval-based architecture.

Product context:

- `ProductContext` defines ARIA as an AI Social Media Manager and Brand Manager with approval-based workflow mode.
- Supported capabilities include strategy, content generation, hashtag recommendation, visual concept generation, calendar planning, community management, reporting, competitor analysis, trend research, and approval workflow.
- Automation boundaries remain explicit: no auto-publish, no auto-reply, no real platform scheduling, and no scraping without future integration.
- `PromptRegistry` injects product context into content, quality, and specialist-agent prompt payloads.

Brand Brain routes:

- `GET /internal/ai/workspace-context`
- `GET /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile`
- `PUT /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile/validate`

The Brand Brain routes return schema-first `BrandProfileResponse` and `BrandProfileValidationResult` objects. They do not expose raw database rows or `brand_profile_json`.

Frontend workspace routes:

- `/dashboard/ai`
- `/dashboard/brand-brain`
- `/dashboard/content-studio`
- `/dashboard/strategy`
- `/dashboard/trends`
- `/dashboard/competitors`
- `/dashboard/ai-analyst`
- `/dashboard/calendar-ai`
- `/dashboard/community-ai`
- `/dashboard/reports-ai`

The frontend client `aria-frontend/lib/api/ai-workspace.ts` calls only the centralized LLM orchestration API. New AI workspace code does not import legacy OpenAI or Anthropic helpers. Existing approval dashboard routes remain unchanged.
