# Phase 8 Product AI Workspace Audit

## Current Product Status

ARIA is not yet a full AI Social Media Manager workspace from the frontend user's point of view. Before Phase 8 it has a strong backend AI orchestration layer, persistence foundation, approval lifecycle, approval queue, and detailed approval review UI. The broader product modules exist mostly as backend capabilities or mock/static dashboard pages.

The current product is best described as an approval-centered AI draft review system with latent strategy, content, calendar, community, reporting, competitor, and trend agents.

Verification update: the Phase 8 workspace foundation now exposes the main AI Social Media Manager modules, including standalone Trends and Competitors panels. Older legacy dashboard pages remain mock/static or direct-provider backed and should be migrated later.

## Backend AI Capabilities Not Fully Exposed In Frontend

The backend already exposes internal schema-first routes for:

- `POST /internal/ai/generate-content-package`
- `POST /internal/ai/brand-strategy`
- `POST /internal/ai/competitors/analyze`
- `POST /internal/ai/trends/research`
- `POST /internal/ai/hashtags/recommend`
- `POST /internal/ai/visual-concept`
- `POST /internal/ai/content-calendar`
- `POST /internal/ai/community/analyze`
- `POST /internal/ai/reports/insights`
- `POST /internal/ai/content-quality/review`

These routes are now represented by typed frontend clients and product-level workspace panels in the Phase 8 workspace. Older legacy dashboard pages still do not use these clients.

## Frontend Pages Still Using Mock, Static, Or Legacy Data

- `/dashboard/brand`: uses dashboard mock/store data and an older AI generator panel.
- `/dashboard/content`: uses mock posts and the older generator panel.
- `/dashboard/create`: uses the older generator panel.
- `/dashboard/analytics`: uses mock analytics charts.
- `/dashboard/scheduler`: uses mock scheduled posts and does not call the AI calendar planner.
- `/dashboard/settings`: displays a mock BrandProfileCard.
- Older route-group pages under `app/(dashboard)` include richer legacy generator/scheduler flows, but they are separate from the active `/dashboard/...` shell and include legacy direct provider paths.

Before Phase 8, the approval pages under `/dashboard/approval` were the only frontend surface clearly wired to the centralized LLM orchestration service.

Phase 8 workspace pages wired to the centralized orchestration service:

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
- `/dashboard/approval`

## Orchestrator Methods Without Frontend API Client Functions

Before Phase 8, frontend API coverage was missing for:

- `generate_content_package`
- `create_brand_strategy`
- `analyze_competitors`
- `research_trends`
- `recommend_hashtags`
- `generate_visual_concept`
- `create_content_calendar`
- `analyze_community_message`
- `generate_report_insights`
- `review_content_quality`

Approval-specific client functions exist in `aria-frontend/lib/api/approval.ts`.

Phase 8 adds typed client coverage for all orchestrator methods in `aria-frontend/lib/api/ai-workspace.ts`.

## AI Agents Unreachable From Frontend

Before Phase 8, the following agents were reachable through backend routes but not through dedicated frontend workspace panels:

- `BrandStrategyAgent`
- `CompetitorAnalysisAgent`
- `TrendResearchAgent`
- `HashtagAgent`
- `VisualConceptAgent`
- `CalendarPlanningAgent`
- `CommunityManagementAgent`
- `ReportingAgent`
- `QualityReviewAgent`
- `ContentGeneratorAgent` through the new backend workflow route

Phase 8 exposes these agents through workspace panels. `CompetitorAnalysisAgent` and `TrendResearchAgent` are available from both the Strategy intelligence flow and standalone Competitors/Trends panels.

## Brand Brain Status

The backend has a schema-first `BrandProfile` and `AIPersistenceRepository.save_brand_profile/load_brand_profile`, but it does not expose internal get/upsert/validate brand profile routes yet.

The frontend has mock brand profile cards and onboarding pages, but no active Brand Brain page that edits the backend `BrandProfile`, shows completeness, or warns when workflows are using mock/default brand context.

## Manual Configuration Needed

The user should manually configure brand-specific data once:

- brand name
- industry
- description
- products/services
- target audience
- tone of voice
- brand values
- approved claims
- forbidden words
- forbidden topics
- competitors
- platforms
- visual style
- business goals
- language preferences

For Phase 8, competitor examples, trend keywords, analytics metrics, campaign briefs, content topics, target platform, community messages, and reporting date ranges remain manual inputs. No scraping or external analytics ingestion is implemented.

## System-Known Product Context

The system should know without asking the user that ARIA is:

- an AI Social Media Manager
- a Brand Manager assistant
- a Content Creator
- an AI Analyst
- an approval-based automation platform

This context should be formalized in backend schemas and prompt context so frontend panels do not ask the user to explain the app's domain.

## Direct Provider Helper Risk

Legacy direct provider paths still exist:

- `aria-frontend/app/api/ai/_lib.ts` imports and uses OpenAI helpers.
- `aria-frontend/lib/openai.ts` constructs an OpenAI client from `OPENAI_API_KEY`.
- `aria-frontend/app/api/generate/route.ts` imports `@anthropic-ai/sdk`.
- `aria-frontend/lib/ai.ts` calls `/api/generate`.

These remain outside the new approval/workspace code. Phase 8 should not import them from new AI workspace files.

## Phase 8 Implementation Scope

Implement now:

- product/workspace context schema and route
- Brand Brain get/upsert/validate backend routes
- typed frontend AI workspace API client for all orchestrator methods
- active `/dashboard/...` panels for AI Workspace Home, Brand Brain, Content Studio, Strategy, Trends, Competitors, AI Analyst, Calendar AI, Community AI, and Reports AI
- navigation entries for the AI workspace modules
- documentation updates and tests/checks

Wait for later phases:

- scraping and social listening ingestion
- social publishing
- automatic replies
- real platform scheduling
- social platform API integrations
- production authentication
- migration of legacy direct provider frontend routes
- full browser/live database verification against the intended pgvector stack

## Files Likely To Change

Backend:

- `aria/apps/llm-orchestration/app/ai/schemas/brand.py`
- `aria/apps/llm-orchestration/app/ai/schemas/__init__.py`
- `aria/apps/llm-orchestration/app/ai/prompts/registry.py`
- `aria/apps/llm-orchestration/app/ai/prompts/system_prompts.py`
- `aria/apps/llm-orchestration/app/ai/agents/orchestrator.py`
- `aria/apps/llm-orchestration/app/main.py`
- new or updated tests under `aria/apps/llm-orchestration/tests`

Frontend:

- `aria-frontend/lib/api/ai-workspace.ts`
- new workspace pages under `aria-frontend/app/dashboard`
- new workspace component(s) under `aria-frontend/components`
- dashboard navigation components
- `aria-frontend/.env.example`

Documentation:

- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `PHASE_8_PRODUCT_AI_WORKSPACE_SUMMARY.md`
