# ARIA Repository Audit

Date: 2026-07-11

Branch: `codex/aria-full-architecture-ui-ux-remediation`

Current remediation commit at audit start: `cf1bdf0`

## Executive Findings

- Canonical frontend runtime is `aria-frontend`; canonical backend runtime is `aria/apps/llm-orchestration`.
- The role-aware frontend shell under `aria-frontend/app/(dashboard)` is the canonical product shell for normal workflows.
- Legacy dashboard routes under `aria-frontend/app/dashboard` still exist and must be retired, redirected, or migrated route by route.
- Direct frontend AI provider routes are now retired with explicit `410 FRONTEND_PROVIDER_ROUTE_RETIRED` responses.
- The backend still has a route monolith in `aria/apps/llm-orchestration/app/main.py`; it initializes the FastAPI app and still owns most business routes.
- Root-level `apps/` and `packages/` overlap with `aria/apps/` and `aria/packages/`; deployment references currently select different trees for different workflows.
- Demo/mock behavior is partially explicit, but hardcoded `brand-1`, `ARIA Labs`, preview auth, and synthetic publishing IDs remain in product-adjacent code.
- Approval aggregate queue behavior had verified contract bugs; this branch fixes cross-type status filtering and global pagination semantics.

## Frontend Route Inventory

### Canonical Role-Aware Shell

| URL | Page file | Layout | API/data path | Auth guard | Decision |
| --- | --- | --- | --- | --- | --- |
| `/posts/new` | `aria-frontend/app/(dashboard)/posts/new/page.tsx` | `app/(dashboard)/layout.tsx` | `generatePost` via `/v1/posts/generate`; AI workspace helper for package generation | client shell/auth context | Canonical Create workflow; oversized and needs feature split |
| `/posts` | `aria-frontend/app/(dashboard)/posts/page.tsx` | `app/(dashboard)/layout.tsx` | content API/client state | client shell/auth context | Canonical Content list |
| `/posts/[post_id]/result` | `aria-frontend/app/(dashboard)/posts/[post_id]/result/page.tsx` | nested post layout | `/v1/posts/{post_id}` style client | client shell/auth context | Canonical generated result detail pending contract sync |
| `/posts/[post_id]/schedule` | `aria-frontend/app/(dashboard)/posts/[post_id]/schedule/page.tsx` | nested post layout | `/v1/schedules` style client | client shell/auth context | Canonical schedule-prep detail; external publishing not proven |
| `/scheduler` | `aria-frontend/app/(dashboard)/scheduler/page.tsx` | `app/(dashboard)/layout.tsx` | schedule API/client state | client shell/auth context | Canonical Calendar planning route |
| `/analytics` | `aria-frontend/app/(dashboard)/analytics/page.tsx` | `app/(dashboard)/layout.tsx` | dashboard/mock analytics paths | client shell/auth context | Canonical Insights destination after data-source labels are enforced |

### Legacy Dashboard Shell

| Route family | Files | Current status | Decision |
| --- | --- | --- | --- |
| Dashboard overview | `app/dashboard/page.tsx`, `components/dashboard/*` | Polished legacy shell with separate nav config | Keep only as canonical Overview after route parity is verified |
| Brand | `app/dashboard/brand/page.tsx`, `app/dashboard/brand-brain/page.tsx` | Duplicate Brand Brain concepts | Consolidate into one Brand Brain destination |
| Creation/content | `app/dashboard/create`, `content`, `content-studio`, `posts` | Duplicates `/posts/new` and `/posts` | Redirected for common overlapping routes; remaining pages need retirement pass |
| Approval | `app/dashboard/approval/*` | Active approval workflow and master/detail UI | Keep as canonical Approval surface for now |
| AI modules | `ai`, `ai-analyst`, `calendar-ai`, `community-ai`, `reports-ai`, `strategy`, `trends`, `competitors` | Module catalogue duplicates Insights/Create functions | Group under Insights or remove until implemented truthfully |
| Admin/settings | `admin`, `settings` | Mixed settings/admin concepts | Consolidate into Settings with real controls only |

### Public/Auth/Onboarding Routes

| Route family | Files | Decision |
| --- | --- | --- |
| `/`, `/overview` | `app/page.tsx`, `app/overview/page.tsx` | Public and overview entry behavior need redirect/auth decision |
| `/login`, `/register`, `/(auth)/signin`, `/oauth/callback` | auth pages and `app/api/auth/*` | Keep one auth surface; remove duplicated sign-in entry after provider decision |
| `/onboarding/*` | brand-assets, company-profile, platforms, quality-check, vocabulary | Keep if backed by `/v1/onboarding/*`; requires contract and auth verification |

## Navigation Inventory

- Canonical target IA: Overview, Brand Brain, Create, Content, Calendar, Approval, Insights, Settings.
- Legacy desktop navigation was reduced to this IA in `aria-frontend/app/dashboard/layout.tsx`.
- Mobile nav was capped to Overview, Create, Content, Approval, More.
- Active matching for `/posts/new` versus `/posts` now uses exact/segment-safe matching in both dashboard shells.
- `aria-frontend/lib/navigation.ts` now centralizes labels, hrefs, icons, role visibility, route matching, mobile primary destinations, and role default redirects.
- Remaining issue: command palette, quick actions, cards, and legacy module links still need a full orphan-link pass.

## Frontend API-Call Inventory

| Source | Destination | Auth behavior | Mock/demo behavior | Decision |
| --- | --- | --- | --- | --- |
| `aria-frontend/lib/api.ts` | `/v1/onboarding/*`, `/v1/posts/*`, `/v1/schedules/*`, `/v1/oauth/*` | bearer/local client helpers | preview fallbacks in some flows | Keep but split by domain and generate contracts |
| `aria-frontend/lib/api/ai-workspace.ts` | `/internal/ai/*` | API key/session headers not fully enforced | default context uses `brand-1` and `ARIA Labs` | Keep as canonical AI workspace client; remove silent demo defaults |
| `aria-frontend/lib/api/approval.ts` | `/internal/ai/approval/*` | same backend-base resolver | no provider mock, but backend may be unconfigured | Keep; now benefits from aggregate queue fix |
| `aria-frontend/context/AuthContext.tsx` | `/api/auth/login`, `/api/auth/register` | local API routes and storage | preview/auth fallback exists | Keep temporarily; align with Supabase Auth before production |
| `aria-frontend/services/aiService.ts` | older `/ai/*` backend paths | none proven | legacy error behavior | Deprecate after caller search |
| `aria-frontend/src/lib/api.ts` | `NEXT_PUBLIC_API_URL` generic client | unknown | unknown | Duplicate tree; remove only after import search and route verification |
| `aria-frontend/app/api/ai/*` and `/api/generate` | retired frontend provider routes | none | no generation | Retired with `410` tombstones |

## Backend Route Inventory

Canonical backend source: `aria/apps/llm-orchestration/app/main.py`.

| Route family | Methods and paths | Auth/authz | Persistence | Status |
| --- | --- | --- | --- | --- |
| Health | `GET /health` | none | no | Keep |
| Workspace/Brand Brain | `GET /internal/ai/workspace-context`, `GET/POST/PUT /internal/ai/brand-profile`, `POST /internal/ai/brand-profile/validate` | not centrally enforced | optional repository | Keep; add auth/tenant boundary |
| Generation | `POST /internal/ai/generate-content-package`, brand strategy, competitors, trends, hashtags, visual concept, calendar, community, reports, content quality | not centrally enforced | optional repository | Keep as canonical AI orchestration surface |
| Approval actions | `POST /internal/ai/approval/decision`, submit, approve, reject, request-changes, archive | reviewer metadata accepted in payload | repository through service | Keep; add authenticated reviewer source and status preconditions |
| Approval detail/audit | `GET /internal/ai/approval/detail/*`, `GET /internal/ai/approval/audit/*` | not centrally enforced | required for detail | Keep; add tenant scoping |
| Approval queues | typed and aggregate queue endpoints | not centrally enforced | required | Fixed aggregate status/pagination; still needs total-count query support |
| Draft aliases | `GET /internal/ai/drafts/content`, calendar, community | not centrally enforced | required | Backward-compatible aliases |
| Legacy captions/run | `/internal/captions/generate`, `/run` | mixed | creates dependencies inside requests | Isolated with deprecation/demo headers; still needs router split |

## LLM-Call Inventory

| Source | Provider/model path | Prompt/schema source | Mock behavior | Decision |
| --- | --- | --- | --- | --- |
| `ai/llm/client.py` | OpenAI chat completions through `https://api.openai.com/v1/chat/completions` | prompt registry and typed agent schemas | `LLMSettings.is_mock_enabled` when `AI_MOCK_MODE=true`, no key, or `replace-me` | Canonical provider gateway |
| `ai/agents/*` | `LLMClient` injected into orchestrator/agents | domain request/response models | deterministic mock client path | Keep |
| `main.py` `LiteLLMAdapter` | no real provider call; returns deterministic captions | legacy `CaptionRequest` | explicitly demo-only; refuses configured provider keys; no fake token usage | Retire after callers are migrated |
| root `apps/*` services | `/v1/llm/proxy/chat` references | service-specific prompts | unknown | Non-canonical unless deployed by root docker-compose |
| frontend provider routes | formerly OpenAI/Anthropic | deleted helpers/tombstones | no generation | Retired |

## Database Inventory

| Location | Contents | Compatibility notes | Decision |
| --- | --- | --- | --- |
| `aria/db/migrations/001_schema.sql` through `009_ai_tables_enable_rls.sql` | ARIA app schema, AI draft tables, approval audit, RLS via `app.company_id`, pgvector extension | Supabase-oriented; active AI backend tables live here | Canonical migration source for current MVP |
| `aria/packages/db/migrations/0001_init.sql` | separate tenant schema, enums, vector tables, RLS via `app.tenant_id`, Timescale references | Conflicts with `aria/db` ownership model | Defer/remove after import and deployment reference audit |
| `aria/scripts/migrations/*` | migration runner helpers | needs runbook alignment | Keep if it targets canonical `aria/db` |
| `aria-frontend/prisma/migrations/*` | frontend-local Prisma schema history | not aligned with FastAPI/Supabase path | Mark legacy until proven active |

## Service Ownership Matrix

| Component | Root path | Nested path | Runtime/deploy reference | Decision |
| --- | --- | --- | --- | --- |
| AI orchestration | none equivalent | `aria/apps/llm-orchestration` | `render.yaml` | Canonical backend |
| API service | `apps/*` microservices | `aria/apps/api` | root `docker-compose.yml` and nested source | Non-canonical for Vercel/Render MVP until product flow requires it |
| Dashboard | none | `aria/apps/dashboard` plus `aria-frontend` | Vercel path is `aria-frontend` | `aria-frontend` is canonical |
| Scheduler | `apps/scheduler` | `aria/apps/scheduler` | root docker-compose and nested source | Defer; scheduling currently planning/readiness unless external platform API confirms |
| Shared types | `packages/types` | `aria/packages/*` | tests/imports vary | Consolidate behind generated OpenAPI contracts |

## Documentation Accuracy Audit

| Statement/source | Classification | Notes |
| --- | --- | --- |
| README Vercel frontend plus Render backend plus Supabase | Implemented but not end-to-end verified in this turn | Local builds pass; provider deploy requires owner access |
| `docs/full-system-architecture.md` external publishing flow with `external_post_id` | Simulated/planned | Code contains synthetic IDs such as `ext_${schedule_id}` |
| `/v1/llm/proxy/chat` service token architecture | Planned or non-canonical | Not the active canonical LLM path for `aria/apps/llm-orchestration` |
| Frontend direct OpenAI/Anthropic generation | Outdated | Routes now return explicit 410 tombstones |
| Approval queue supports aggregate inbox | Implemented and regression-tested | Cross-type status and global pagination repaired in this branch |
| Live analytics/trend/competitor integrations | Not fully verified | UI must label source as demo/manual/mock unless external integrations are proven |

## Security And Auth Findings

- Frontend auth still uses local API routes and token storage patterns; this is not sufficient backend authorization.
- `/internal/ai/*` backend routes do not yet enforce authenticated identity, tenant ownership, or role checks centrally.
- Reviewer identity can still be supplied by request metadata in approval actions.
- Supabase appears to be the intended deployment/auth direction; introducing a second identity provider would increase drift.

## UI/UX And Accessibility Findings

- The canonical navigation map is now consistent at the primary level.
- Oversized UI files remain: `posts/new/page.tsx`, `ApprovalDashboard.tsx`, and `AIWorkspacePanels.tsx` should be split by workflow step, server-state hook, dialogs, and panels.
- Browser screenshots were captured for `/posts/new`, `/posts`, `/dashboard/brand`, and `/dashboard/approval` at desktop and mobile sizes.
- Approval UI correctly shows backend unavailable state locally when the FastAPI service is not running.
- A full keyboard/focus/contrast audit still needs Playwright/a11y coverage after the duplicated route set is reduced.

## Remediation Completed On This Branch

- Established explicit canonical architecture notes in `docs/architecture/CANONICAL_ARCHITECTURE.md`.
- Retired direct frontend provider routes with 410 responses.
- Removed frontend provider SDK dependencies.
- Fixed `/posts/new` versus `/posts` active-route collision.
- Reduced legacy navigation to the target IA and mobile cap.
- Consolidated duplicated navigation arrays into one typed source of truth.
- Added overlap redirects from legacy dashboard content/create routes.
- Repaired aggregate approval queue status filtering and global pagination behavior.
- Added backend regression tests for approval aggregate status and pagination.
- Isolated legacy caption/provider behavior behind demo/deprecation headers and regression tests.

## Remaining Phase Decisions

1. Split `main.py` into routers and dependency modules without changing public contracts.
2. Generate TypeScript contracts from FastAPI OpenAPI, then delete duplicated handwritten types where safe.
3. Remove or isolate legacy `LiteLLMAdapter` and `/run` behavior.
4. Replace preview/hardcoded brand context with authenticated organization/brand selection.
5. Convert root `apps/` and duplicate packages into clearly documented deferred services or remove after reference audit.
6. Add authenticated tenant/role enforcement before any production claim.
7. Add end-to-end UI and accessibility tests after route consolidation.
