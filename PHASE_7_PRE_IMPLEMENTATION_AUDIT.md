# Phase 7 Pre-Implementation Audit

## Current Backend Status

The LLM orchestration service has working Phase 1-6 foundations:

- Schema-first AI agents and orchestrator methods are under `aria/apps/llm-orchestration/app/ai`.
- `BrandMemory` can use `AIPersistenceRepository` when a runtime DB pool exists.
- Persistence tables for brand memory, content drafts, quality reviews, calendar draft items, community reply drafts, report drafts, and approval audit events are defined in migrations `007` and `008`.
- Approval lifecycle schemas, transition validation, service methods, and route handlers exist.
- Phase 5 queue DTOs hide raw JSONB fields and expose frontend-safe list data.
- Existing backend tests use fake repositories and optional live Postgres tests, keeping normal tests independent of local DB credentials.

Known backend risk remains: full `python -m db.migrate` is still not verified against the intended pgvector Docker stack. Direct AI migrations `007` and `008` were previously verified on a temporary real Postgres instance, but the full runner is blocked when pgvector is unavailable.

## Current Frontend Status

The active dashboard shell lives under `aria-frontend/app/dashboard` and includes Sidebar, TopBar, and MobileNav. Phase 6 added:

- `/dashboard/approval` and type-specific approval queue routes.
- `aria-frontend/lib/api/approval.ts`.
- `aria-frontend/components/approval/ApprovalDashboard.tsx`.
- Dashboard approval navigation.

The current approval UI is useful for queue review, action submission, and audit display, but it only renders queue DTO preview fields. It does not yet load full safe detail DTOs.

## Contract Gaps

- No backend detail endpoints exist for content, calendar, community reply, or report drafts.
- Frontend selected-item details are based on list DTO fields only.
- Request-changes data is persisted through audit events, but there is no explicit detail/timeline DTO presenting latest reason and requested changes.
- The frontend request-changes dialog does not require a reason or at least one requested change.
- LLM orchestration service has no CORS middleware, while the browser approval client calls it directly.

## Detail And Revision DTO Gaps

Needed backend DTOs:

- `ContentDraftDetail`
- `CalendarDraftDetail`
- `CommunityReplyDraftDetail`
- `ReportDraftDetail`
- `ApprovalAuditTimeline`

The existing database rows contain raw JSONB fields such as `content_package_json`, `quality_scores_json`, `calendar_item_json`, `insight_payload_json`, and `metadata_json`. These should be parsed inside the backend and mapped into curated review fields only. The frontend should never receive or render these raw DB fields.

Migration need: none expected for Phase 7. Migration `008` already stores `reason`, `requested_changes`, reviewer fields, timestamps, object type, and object id in `ai_approval_audit_events`.

## Deployment, CORS, Auth, Env Risks

- `aria-frontend/lib/api/approval.ts` reads `NEXT_PUBLIC_AI_ORCHESTRATION_URL`, `NEXT_PUBLIC_API_BASE_URL`, and `NEXT_PUBLIC_API_URL`, but `aria-frontend/.env.example` does not document `NEXT_PUBLIC_AI_ORCHESTRATION_URL`.
- The main ARIA backend has CORS middleware in `aria/app/main.py`, but `aria/apps/llm-orchestration/app/main.py` does not.
- Frontend auth is localStorage/JWT based. Approval client sends bearer tokens from local/session storage if present, but backend approval routes do not enforce production auth yet.
- Reviewer identity is optional. Phase 7 should use explicit placeholder reviewer fields only and document production auth as later work.

## Direct OpenAI And Anthropic Frontend Risk Status

Legacy direct provider paths still exist:

- `aria-frontend/app/api/ai/_lib.ts` imports `OpenAI` and uses `getOpenAIClient`.
- `aria-frontend/lib/openai.ts` constructs an OpenAI client.
- `aria-frontend/app/api/generate/route.ts` imports `@anthropic-ai/sdk`.

The Phase 6 approval client does not import those helpers. Phase 7 must preserve that isolation and avoid direct provider calls from new approval code.

## Test Coverage Gaps

Backend gaps:

- Detail DTO mapping should prove raw JSONB fields are not exposed.
- Detail routes should cover content, calendar, community, and report responses.
- Missing detail objects should return `404`.
- Invalid generic detail object type should return `400`.
- Missing persistence should return `503`.
- Detail responses should include audit timelines and latest requested changes.
- Request-changes should preserve reason and requested changes in audit responses.

Frontend gaps:

- No frontend test runner is configured.
- TypeScript/build validation is available.
- Lint is not usable non-interactively because `next lint` asks to configure ESLint.
- Source searches should guard approval code against provider imports, raw JSONB fields, forbidden lifecycle terminal states, social API integrations, and hardcoded secrets.

## Files Likely To Change

Backend:

- `aria/apps/llm-orchestration/app/ai/approval/queue.py`
- `aria/apps/llm-orchestration/app/main.py`
- `aria/apps/llm-orchestration/tests/test_phase_5_approval_queue.py` or a new Phase 7 test file

Frontend:

- `aria-frontend/lib/api/approval.ts`
- `aria-frontend/components/approval/ApprovalDashboard.tsx`
- `aria-frontend/.env.example`

Documentation:

- `PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md`
- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `PHASE_4_API_CONTRACTS.md`

## Exact Implementation Plan

1. Add safe detail DTOs, timeline DTO, and row-to-detail mappers in the backend approval DTO module.
2. Add generic and type-specific detail routes under `/internal/ai/approval/detail`.
3. Add minimal CORS middleware to LLM orchestration using `CORS_ORIGINS`, matching the main backend pattern.
4. Add tests for detail DTO safety, route shape, missing object, invalid object type, missing persistence, audit timeline, and request-changes preservation.
5. Extend the frontend approval API client with detail DTO types and detail fetchers.
6. Update the approval dashboard selected-item panel to load safe detail, render full review fields, show audit timeline, and validate request changes.
7. Document env variables and deployment/auth/CORS findings.
8. Run backend tests, frontend typecheck/build, and source safety scans.

## What Should Not Be Implemented In Phase 7

- Scraping.
- Social media publishing.
- Automatic replies.
- Real platform scheduling.
- Social platform API integrations.
- Direct OpenAI/Anthropic calls from approval frontend code.
- Raw database JSONB exposure in frontend UI.
- Fake production authentication.
- Hardcoded secrets.
- Database volume resets or destructive migration changes.
- Full frontend/backend rewrites.
- Deletion of duplicate app folders or historical snapshot files.
