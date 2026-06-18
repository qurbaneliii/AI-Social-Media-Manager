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

