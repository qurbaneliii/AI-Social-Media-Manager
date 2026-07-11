# ARIA Migration And Deprecation Plan

Date: 2026-07-11

Detailed phase rollback entries are tracked in `docs/audits/ARIA_MIGRATION_ROLLBACK_LOG.md`.

## Current Branch

`codex/aria-full-architecture-ui-ux-remediation`

## Active Deprecations

| Area | Deprecated path | Canonical path | Current action |
| --- | --- | --- | --- |
| Frontend AI provider routes | `/api/generate`, `/api/ai/*` generation helpers | backend `/internal/ai/*` and `/v1/posts/generate` | Return `410 FRONTEND_PROVIDER_ROUTE_RETIRED` |
| Create routes | `/dashboard/create`, `/dashboard/content-studio` | `/posts/new` | Redirect configured |
| Content routes | `/dashboard/content`, `/dashboard/posts` | `/posts` | Redirect configured |
| Scheduler route | `/dashboard/scheduler` | `/scheduler` | Redirect configured |
| Analytics route | `/dashboard/analytics` | `/analytics` | Redirect configured |
| Navigation arrays | local arrays in layouts/sidebar/mobile nav | `aria-frontend/lib/navigation.ts` | Consolidated |
| Legacy caption route | `/internal/captions/generate` | `/internal/ai/generate-content-package` or canonical generation contract | Explicit demo/deprecated headers |
| Legacy orchestration route | `/run` | canonical `/internal/ai/*` and `/v1/*` flows | Explicit deprecated header |
| Legacy provider adapter | `LiteLLMAdapter` in `main.py` | `ai/llm/client.py` via `AIOrchestrator` | Refuses configured provider keys |
| Legacy AI assist URLs | `/ai/generate-content`, `/ai/generate-batch`, `/ai/improve-content`, `/ai/analyze-content`, `/ai/suggest-hashtags`, `/ai/suggest-topics` | `/internal/ai/*` on the public FastAPI backend | Frontend adapter migrated |
| Split public API env vars | `NEXT_PUBLIC_AI_ORCHESTRATION_URL`, `NEXT_PUBLIC_API_URL` | `NEXT_PUBLIC_API_BASE_URL` | Removed from active runtime clients |

## Removal Rules

Before removing or moving a file, run repository searches for:

- static imports;
- dynamic imports;
- route references;
- Docker references;
- workflow references;
- package scripts;
- documentation links;
- tests;
- deployment manifests.

## Rollback Strategy

- Each remediation phase must be independently revertible by commit.
- No production database migrations are rewritten.
- Data-affecting migrations must be additive and reversible where possible.
- Compatibility tombstones may remain until external consumers are proven absent.
