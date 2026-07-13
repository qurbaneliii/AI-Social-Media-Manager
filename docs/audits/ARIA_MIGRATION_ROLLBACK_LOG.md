# ARIA Migration And Rollback Log

Date: 2026-07-11

Branch: `codex/aria-full-architecture-ui-ux-remediation`

## Log

| Phase | Change | Forward action | Rollback action | Verification |
| --- | --- | --- | --- | --- |
| 0 | Baseline captured | Added `docs/audits/ARIA_BASELINE_REPORT.md` | Revert docs-only audit commit | Baseline commands recorded |
| 1 | Frontend provider routes retired | Keep route tombstones returning `410 FRONTEND_PROVIDER_ROUTE_RETIRED` | Restore deleted provider helpers and route implementations from pre-branch commit if product decision changes | HTTP smoke verified 410 responses |
| 1 | Canonical navigation selected | Legacy dashboard nav reduced to target IA and mobile cap | Revert layout/nav edits | Browser screenshots for dashboard and role-aware routes |
| 1 | Mobile More navigation repaired | `More` opens a bottom-sheet menu populated from canonical secondary navigation items | Revert `MobileNav.tsx` and `lib/navigation.ts` changes for this phase | `npm run typecheck`; `npm run lint`; `npm run build`; browser smoke at `390 x 844` |
| 1 | Duplicate route redirects | Added redirects from overlapping `/dashboard/create`, `/dashboard/content*`, posts, scheduler, analytics paths | Remove redirect entries in `aria-frontend/next.config.js` | HTTP smoke verified redirect status |
| 1 | Render env cleanup | Removed fake `OPENAI_API_KEY=replace-me` value and set Render branch to `main` | Restore previous render.yaml values only for an explicitly documented preview environment | `npm run build`; docs verification |
| 2 | Approval aggregate queue repair | Aggregate queue now skips inapplicable object types for cross-type status filters and paginates after global sort | Revert `main.py` approval queue helper changes and regression tests | `pytest aria/apps/llm-orchestration/tests/test_phase_5_approval_queue.py -q` |
| 7 | Public runtime router extraction | Moved public `/v1/posts/*`, `/v1/companies/{company_id}/posts`, and `/v1/schedules/*` routes to `api/routers/public_runtime.py`; moved shared runtime dependencies to `api/dependencies.py` | Revert router extraction commit to restore inline `main.py` route definitions | `ruff`; public runtime contract tests; full llm-orchestration tests; Render-style local smoke |
| 7 | Brand Brain workspace router extraction | Moved workspace context and Brand Profile GET/POST/PUT/validation routes to `api/routers/workspace.py` while preserving shared dependency overrides and error handling | Revert the workspace router extraction commit to restore inline `main.py` route definitions | `ruff`; Phase 8 product workspace tests; full llm-orchestration tests; Render-style local smoke |
| C/D | Canonical browser API base and route contract cleanup | Centralized active clients on `NEXT_PUBLIC_API_BASE_URL`, removed legacy aliases, strengthened Render method/path assertions, and retired unmounted media/import controls | Revert this slice to restore alias resolution and legacy controls only if the public backend also regains authenticated media/import ownership | frontend typecheck, lint, build; public runtime contract tests; active-client source scan |
| PR9 backend | Tenant/auth foundation | Added workspace, membership, and brand ownership; JWT issuer/audience verification; database-derived roles | Revert commits before applying migration 010; after migration, restore application code first and retain tenant columns until data export is complete | Backend tests, frontend typecheck/lint/tests |
| PR9 backend | Persistent product workflows | Replaced process-memory post/calendar stores and legacy approval client paths with tenant-scoped PostgreSQL repositories and `/v1` routers | Revert clients and routers; do not drop persisted records during application rollback | Repository contract tests; live PostgreSQL migration transaction rolled back |
| PR9 backend | OpenAPI contract sync | Added exported OpenAPI JSON and generated TypeScript schema with CI drift check | Remove generated client import and scripts only after restoring equivalent handwritten contracts | `npm run contracts:generate`; frontend typecheck |
| PR9 backend | Deployment truthfulness | Render readiness now requires PostgreSQL; mock mode defaults off; Pages deployment is manual preview-only | Restore prior health path only if deployment accepts a non-ready backend; never restore implicit mock fallback | Render config review; backend LLM tests |

## Current Rollback Boundaries

- No production database migrations have been applied by this branch. Migration 010 was executed against live PostgreSQL inside an explicit transaction and rolled back successfully.
- No data-destructive commands have been run.
- Provider-route retirement is intentionally reversible through git because the old behavior was unsafe for the canonical architecture but may still be useful for forensic comparison.
- Approval queue response shape was kept stable: `items`, `count`, `limit`, and `offset` remain unchanged.

## Pending Migration Notes

- Generated FastAPI contracts are committed. Remaining UI-specific DTOs may stay handwritten, but canonical capability contracts already import generated types.
- When removing duplicate root services, first prove they are not referenced by Docker Compose, GitHub Actions, Render, Vercel, package scripts, tests, or documentation.
- When replacing preview auth with Supabase Auth, preserve a separately named demo mode that cannot be mistaken for authenticated production mode.
