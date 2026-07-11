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

## Current Rollback Boundaries

- No production database migrations have been applied by this branch.
- No data-destructive commands have been run.
- Provider-route retirement is intentionally reversible through git because the old behavior was unsafe for the canonical architecture but may still be useful for forensic comparison.
- Approval queue response shape was kept stable: `items`, `count`, `limit`, and `offset` remain unchanged.

## Pending Migration Notes

- When TypeScript contracts are generated from FastAPI OpenAPI, keep the previous handwritten contracts until all imports are moved and typecheck/build pass.
- When removing duplicate root services, first prove they are not referenced by Docker Compose, GitHub Actions, Render, Vercel, package scripts, tests, or documentation.
- When replacing preview auth with Supabase Auth, preserve a separately named demo mode that cannot be mistaken for authenticated production mode.
