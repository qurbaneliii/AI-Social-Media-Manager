# AI Architecture Audit

## PDF Summary

The PDF defines ARIA as an approval-based AI Social Media Manager and Brand Manager. The system should support strategy, competitor and trend research, platform-specific content generation, planning, community-management drafts, analytics, reporting, brand-risk controls, and human approval. It explicitly rejects a single monolithic chatbot and requires a modular AI architecture with an AI Orchestrator, Brand Brain/Brand Memory, specialist agents, centralized LLM access, schema-driven structured outputs, versioned prompts, quality evaluation, and safety guardrails.

Phase 1 is limited to the AI/model architecture foundation: orchestrator, centralized OpenAI/LLM client, prompt registry, schemas, brand profile memory structure, base agent structure, content-generation workflow skeleton, quality-review workflow skeleton, mock mode, env documentation, and basic tests.

## Current Repository Summary

The repository already contains a broad ARIA platform skeleton:

- `aria/`: Python/FastAPI microservices, database repositories, Temporal workflows, platform adapters, Kafka schemas, infra files, and an existing `apps/llm-orchestration` service.
- `apps/`: separate Python service folders for caption generation, content analysis, hashtag SEO, audience targeting, visual understanding, scheduler, and time optimization.
- `aria-frontend/`: Next.js dashboard with onboarding, generation, scheduling, posts, analytics, and mock/frontend AI helpers.
- `packages/`: shared prompt templates, decision logic, and typed contracts.
- `docs/full-system-architecture.md`: a strong high-level architecture reference.

Useful pieces include existing service boundaries, Pydantic models, prompt-template package, decision logic tests, frontend approval-oriented screens, and existing architecture docs. Weak areas include duplicate app trees, mixed naming conventions, scattered prompt/LLM proxy behavior, partial orchestration, mock/demo code interleaved with production code, and no clear schema-first agent layer.

## Keep / Refactor / Delete / Add Matrix

| File/Folder | Current Purpose | Decision | Reason | Priority |
|---|---|---:|---|---:|
| `aria/apps/llm-orchestration` | Python FastAPI orchestration service | Refactor | Best home for AI orchestrator, central LLM client, structured output parsing | P0 |
| `aria/apps/llm-orchestration/app/main.py` | Existing orchestration endpoints | Refactor | Preserve `/run`, add schema-first AI endpoint and gradually move old logic behind agents | P0 |
| `aria/apps/llm-orchestration/app/ai` | New AI foundation | Add | Required by PDF for clean AI separation | P0 |
| `aria/.env.example` and root `.env.example` | Environment templates | Refactor | Add OpenAI/mock-mode config without secrets | P0 |
| `docs/full-system-architecture.md` | Existing system architecture | Keep | Useful high-level service/data-flow reference | P0 |
| `packages/prompt-templates` | Existing reusable prompts | Refactor | Keep, but align with new prompt registry/versioning pattern over time | P1 |
| `packages/types` and `aria/packages/python-contracts` | Shared contracts | Refactor | Useful but partially duplicated; consolidate later | P1 |
| `aria/db/repositories/brand_profiles.py` | Brand profile persistence | Keep | Good future backing store for Brand Memory | P1 |
| `aria/memory` | Learning and brand memory jobs | Refactor | Should integrate behind `BrandMemory` facade | P1 |
| `aria/apps/*` service stubs | Microservice skeletons | Keep | Match target modular architecture | P1 |
| root `apps/*` service tree | Parallel app structure | Refactor | Duplicates `aria/apps`; needs ownership decision before deletion | P1 |
| `aria-frontend` | Next.js dashboard | Keep | Provides user-facing approval, generation, scheduling, analytics surfaces | P1 |
| `aria-frontend/lib/openai.ts`, `lib/ai.ts`, API AI routes | Frontend/server AI helpers | Refactor | Avoid direct/random OpenAI calls; route through backend AI orchestration | P1 |
| `modified-files-full-code.md` | Large snapshot/document dump | Delete | Not runtime code; should be removed after confirming it is not needed as historical evidence | P2 |
| deployment scripts at root | Local/deploy helpers | Keep | Useful operationally; no Phase 1 changes needed | P2 |
| social platform adapters | Publishing integration skeletons | Keep | Do not implement or activate publishing in Phase 1 | P2 |

## AI Architecture Problems

- Existing LLM orchestration is partly monolithic and service-call oriented rather than agent/workflow oriented.
- Prompt usage exists in multiple places without a single source of truth for versioning.
- Structured output exists in pockets, but there is no unified schema set for brand profile, content package, community analysis, calendar items, and quality review.
- Brand memory exists as repositories/jobs but not as a clear AI-facing facade.
- No explicit base agent contract or orchestrator methods for the PDF-required workflows.
- LLM provider abstraction is too shallow and currently returns deterministic placeholder output.
- No token/cost tracking hook beyond basic token estimates.
- Guardrails and quality review are not first-class orchestration steps.
- Frontend and backend both contain AI helpers, increasing the risk of scattered model calls.
- Test coverage exists for many service modules but not for the new AI foundation path.

## Proposed Target Architecture

The target AI layer lives under `aria/apps/llm-orchestration/app/ai`:

- `llm/`: central model client, settings, errors, provider types, retry and mock-mode behavior.
- `prompts/`: versioned prompt registry with system, task, platform, and review prompts.
- `schemas/`: Pydantic contracts for brand profile, content requests, generated packages, community analysis, calendars, analytics, and quality evaluation.
- `memory/`: brand memory facade, initially schema-backed and later connected to PostgreSQL/pgvector.
- `agents/`: base agent plus specialist agents. Phase 1 includes content generation and quality review skeletons.
- `workflows/`: approval-based workflows that compose agents and memory.
- `evaluation/`: scoring and validators for safety/approval decisions.

Data flow for Phase 1:

1. API receives `ContentRequest`.
2. `AIOrchestrator.generate_content_package` loads brand context through `BrandMemory`.
3. `PromptRegistry` builds versioned messages.
4. `LLMClient` calls OpenAI or mock mode.
5. Pydantic validates the structured `GeneratedContentPackage`.
6. `QualityReviewAgent` reviews the package.
7. Orchestrator returns a package with `quality_scores` and human-review status.

## Implementation Plan

| Phase | Scope | Priority |
|---|---|---:|
| Phase 1 | AI foundation: orchestrator, LLM client, prompt registry, schemas, brand memory facade, base agents, content package workflow, quality review, mock mode, env, tests | P0 |
| Phase 2 | Implement specialist agents: BrandStrategy, CompetitorAnalysis from provided data, TrendResearch from provided datasets, Hashtag, VisualConcept, CalendarPlanning, CommunityManagement, Reporting | P1 |
| Phase 3 | Connect BrandMemory to `brand_profiles`, approved claims, vocabulary, campaign history, and future vector retrieval | P1 |
| Phase 4 | Expand content workflows into multi-platform packages, variants, visual briefs, calendars, and approval queues | P1 |
| Phase 5 | Analytics/reporting agent with chart-ready structures and next-action recommendations | P1 |
| Phase 6 | Backend integration: Core API endpoint contracts, service auth, persistence, audit logging, async workflow events | P1 |
| Phase 7 | Frontend integration: dashboard calls orchestration endpoint, display quality/risk scores, approval UX | P1 |
| Phase 8 | Evaluation and hardening: token/cost tracking, prompt version metrics, safety policies, regression evals, observability | P2 |


## Re-Audit Update - 2026-06-19

The repository was re-audited against the PDF prompt after cloning `qurbaneliii/AI-Social-Media-Manager`.

Confirmed Phase 1 foundation:

- `aria/apps/llm-orchestration/app/ai/agents/orchestrator.py` exposes the required orchestrator methods and a working `generate_content_package` path.
- `aria/apps/llm-orchestration/app/ai/llm/client.py` centralizes LLM access, mock mode, structured output parsing, metadata hooks, and retry handling.
- `aria/apps/llm-orchestration/app/ai/prompts` centralizes versioned system, platform, task, and quality-review prompts.
- `aria/apps/llm-orchestration/app/ai/schemas` defines the required brand, content, calendar, community, analytics, and evaluation schemas.
- `aria/apps/llm-orchestration/app/ai/memory/brand_memory.py` provides the schema-first Brand Memory facade.
- `aria/apps/llm-orchestration/tests` includes schema, prompt registry, orchestrator, and specialist-agent mock-mode coverage.
- Root `.env.example` and `aria/.env.example` include `OPENAI_API_KEY`, `OPENAI_MODEL`, `AI_MOCK_MODE`, and `AI_TEMPERATURE`.

Implemented during this re-audit:

- Connected real OpenAI retry behavior to `AI_MAX_RETRIES` instead of using a hardcoded retry count.
- Added a test proving that retry attempts follow the configured value.
- Documented retry semantics and local mock-mode execution in `AI_ARCHITECTURE.md`.

Remaining risks:

- `aria-frontend/app/api/ai/_lib.ts` and `aria-frontend/lib/openai.ts` still provide a frontend/server-side OpenAI helper path. This should be refactored in the next phase so frontend AI routes call the backend LLM orchestration service instead of owning model access.
- Duplicate service trees exist under root `apps/` and `aria/apps/`. They should not be deleted until ownership and deployment paths are confirmed.
- `modified-files-full-code.md` still appears to be a large historical snapshot rather than runtime code; deletion should wait for explicit confirmation.

## Phase 4 Audit Update - 2026-06-19

Phase 4 changed the architecture from a planned approval queue concept into backend approval lifecycle contracts under `aria/apps/llm-orchestration/app/ai/approval`.

Implemented architecture pieces:

- Central approval lifecycle schemas, transition validation, service layer, and errors.
- Repository methods for draft lookup/status updates, community reply draft storage, and approval audit event storage/listing.
- Internal API contracts for approval decisions, action routes, audit history, and draft listings.
- Migration `aria/db/migrations/008_ai_approval_lifecycle.sql` for lifecycle constraints, community reply drafts, report drafts, and approval audit events.

Safety posture:

- No frontend UI was added.
- No scraping, publishing, platform scheduling, social API calls, or automatic replies were added.
- `approved` remains an internal approval state only.
- `ready_for_scheduling` remains an internal readiness state only.
- Community reply drafts keep `auto_reply_allowed=false`.

Remaining risk:

- Phase 3.5 live Postgres verification failed because local credentials were invalid, so migrations `007` and `008` still need live database verification with a valid `DATABASE_URL`.

## Phase 5 Audit Update - 2026-06-19

Phase 5 added frontend-ready backend approval queue DTOs while keeping the system backend-only and approval-based.

Implemented architecture pieces:

- Stable queue DTOs in `aria/apps/llm-orchestration/app/ai/approval/queue.py`.
- Sanitized queue routes under `/internal/ai/approval/queue...`.
- Legacy `/internal/ai/drafts/...` routes now return DTO-shaped queue responses instead of raw DB rows.
- Repository queue filtering for brand, status, platform, created date range, limit, and offset.
- Optional live DB test for real asyncpg persistence and approval lifecycle.

Live verification status:

- Direct live application of AI migrations `007` and `008` passed on a temporary isolated Postgres instance on port `5433`.
- Real asyncpg flow for brand memory, content drafts, quality reviews, calendar drafts, community reply drafts, report drafts, approval transitions, and audit events passed.
- Full `db.migrate` remains unverified because the available local Postgres install lacks pgvector and Docker is unavailable.

Remaining risk:

- Before production-like frontend integration, the intended `aria/docker-compose.yml` pgvector stack should run successfully with `python -m db.migrate` so `schema_migrations` is populated through the official migration runner.

## Phase 6 Audit Update - 2026-06-19

Phase 6 implemented the frontend approval dashboard against the Phase 5 queue DTOs and lifecycle routes.

Implemented architecture pieces:

- Typed frontend client at `aria-frontend/lib/api/approval.ts`.
- Approval queue pages under `/dashboard/approval` for all, content, calendar, community, and report drafts.
- Queue filters, detail panels, audit history, lifecycle actions, quality/risk summaries, and explicit safety labels.
- Navigation entries in the dashboard sidebar, command palette, and mobile navigation.
- Deprecation comments on legacy direct OpenAI helpers for new approval workflow use.

Validated behavior:

- Frontend TypeScript validation passed.
- Production frontend build passed after replacing an existing Unix-only postbuild shell command with a portable Node command.
- Backend test suite passed with `42 passed, 2 skipped`.
- Approval frontend source is isolated from direct provider calls and raw persistence JSON field names.

Remaining risks:

- The project has no ESLint configuration, so `npm run lint` starts the interactive Next.js setup prompt instead of running a lint check.
- Full `db.migrate` verification on the intended pgvector stack remains pending.
- Legacy frontend AI routes still contain direct provider integrations and require a separate migration plan.

## Phase 7 Audit Update - 2026-06-27

Phase 7 hardened the approval workflow detail/review layer while keeping the system approval-only.

Implemented architecture pieces:

- Safe approval detail DTOs for content drafts, calendar items, community reply drafts, and report drafts.
- Detail routes under `/internal/ai/approval/detail/...` with typed responses, missing-object handling, invalid object-type handling, persistence-unavailable handling, and latest audit timeline data.
- Request-changes review context surfaced through detail DTOs and frontend validation.
- Frontend approval dashboard detail UX that consumes typed detail DTOs instead of persistence rows.
- Deployment-facing approval client configuration through `NEXT_PUBLIC_AI_ORCHESTRATION_URL` with fallback to the existing frontend API base URL variables.
- Minimal development CORS support in the LLM orchestration FastAPI app through `CORS_ORIGINS`.

Validated behavior:

- Backend tests passed with Phase 7 detail route and DTO coverage.
- Frontend TypeScript validation passed.
- Frontend production build passed.
- Approval frontend source does not import direct OpenAI/Anthropic helpers and does not reference raw persistence JSON field names.

Remaining risks:

- The intended pgvector Docker stack and full `python -m db.migrate` run remain unverified in this environment.
- Optional live Postgres tests still require a valid pgvector-enabled `DATABASE_URL`.
- Legacy direct provider-backed frontend generation routes remain outside the new approval workflow and need a separate migration plan.
- Production authentication is still not implemented for approval reviewer identity; reviewer fields remain explicit request metadata.

## Phase 8 Audit Update - 2026-06-27

Phase 8 expands ARIA from an approval-centered review UI into a broader AI Social Media Manager and Brand Manager workspace.

Implemented architecture pieces:

- Product/workspace context schema through `ProductContext`.
- Prompt payload injection of ARIA's product role, supported capabilities, safety rules, and automation boundaries.
- Brand Brain backend routes for workspace context, brand profile get/upsert/update, and completeness validation.
- Frontend typed AI workspace client for all orchestrator methods.
- Active dashboard panels for AI Workspace, Brand Brain, Content Studio, Strategy, Trends, Competitors, AI Analyst, Calendar AI, Community AI, and Reports AI.
- Navigation updates across sidebar, command palette, and mobile nav.

Safety posture:

- New AI workspace frontend code calls only the centralized LLM orchestration service.
- No scraping, publishing, automatic replies, real platform scheduling, or social platform API integrations were added.
- Brand Brain exposes curated schema fields only and does not expose raw persistence JSON.
- Existing approval dashboard behavior remains intact.

Remaining risks:

- Brand Brain save/load requires `DATABASE_URL` and a configured runtime DB pool; without it the frontend shows a structured backend/persistence error and uses validated default context locally.
- Full pgvector migration-runner verification remains pending.
- Legacy direct OpenAI/Anthropic frontend generator routes remain outside the new workspace and should be migrated in a compatibility-tested phase.
- Production auth/reviewer identity propagation remains future work.
