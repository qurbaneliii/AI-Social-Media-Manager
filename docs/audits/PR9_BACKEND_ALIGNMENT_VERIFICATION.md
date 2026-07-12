# PR #9 Backend Alignment Verification

Date: 2026-07-12

Branch: `codex/aria-final-ui-ux-redesign`

Starting backend-alignment SHA: `ba6c1155cb10801f59dde7946859f93d4cb2d3a4`

## Implemented Boundary

- Canonical frontend: `aria-frontend`.
- Canonical backend: `aria/apps/llm-orchestration`.
- Canonical browser configuration: `NEXT_PUBLIC_API_BASE_URL`.
- Auth: shared signed JWT contract; FastAPI verifies subject, issuer, audience, issued time, and expiry.
- Authorization: role and workspace access are loaded from `ai_workspace_memberships`.
- Persistence: Brand Brain, generated variants, user drafts, Content, internal Calendar, Approval, Overview, Insights, capabilities, and audit use tenant-scoped PostgreSQL repositories.
- External scheduling, publishing, analytics, media storage, and background workers remain explicitly unavailable.

## Canonical Routes

| Product surface | Backend contract |
| --- | --- |
| Session | `GET /v1/session` |
| Brand Brain | `GET/PUT /v1/brands/{brand_id}/profile`; `POST .../validate` |
| Create | `POST /v1/posts/generate`; `POST /v1/posts/drafts` |
| Content | `GET /v1/content`; compatibility reads under `/v1/posts/*` use the same repository |
| Approval | `GET /v1/approval/queue`; detail/audit; atomic decision actions |
| Calendar | `GET/POST/PATCH/DELETE /v1/calendar/items`; `GET /v1/calendar/unscheduled` |
| Overview | `GET /v1/overview` |
| Insights | `GET /v1/insights`; `GET /v1/audit` |
| Settings | `GET /v1/capabilities` |

## Security Properties

- Client-supplied reviewer identity and role are ignored.
- Approval state change and trusted audit insertion occur in one transaction under `FOR UPDATE`.
- Repeated approval decisions return the prior matching event instead of inserting duplicate audit rows.
- Aggregate approval pagination applies after a globally sorted union and reports total matching rows.
- Canonical queries include `workspace_id`; cross-workspace object IDs return not found or forbidden.
- Production legacy approval and `/run` endpoints return `410 LEGACY_ROUTE_RETIRED`.
- Other remaining internal AI tools require a verified token, workspace membership, and matching brand context.
- Unhandled exceptions return a sanitized structured error with a request ID.

## Database Verification

`aria/db/migrations/010_pr9_backend_alignment.sql` was submitted to the connected Supabase PostgreSQL engine as:

```sql
BEGIN;
-- exact migration contents
ROLLBACK;
SELECT 'migration_010_validated_and_rolled_back';
```

Result: `migration_010_validated_and_rolled_back`.

The migration was not persisted because the connected project exposes only its default branch. Applying it permanently requires an isolated development branch or explicit production migration authority.

## Verification Results

| Command | Result |
| --- | --- |
| `python -m ruff check aria/apps/llm-orchestration/app aria/apps/llm-orchestration/tests` | Passed |
| `python -m pytest aria/apps/llm-orchestration/tests -q` | Passed; 2 live-DB suites skipped without `DATABASE_URL` |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed |
| `npm test` | Passed; 5 tests |
| `npm run contracts:generate` | Passed |
| `npm audit --omit=dev` | Passed; 0 runtime vulnerabilities |
| `npm run build` | Passed; exit 0; Next 15.5.20 compiled in 38s and generated 49/49 pages |
| Production-built preview browser matrix | Passed; 96/96 across eight routes, six viewports, light and dark |

Permanent migration and application-level live persistent end-to-end tests remain gated because the connected Supabase project exposes only its default branch and no database connection credential is available to the local runtime. The exact migration passed live PostgreSQL validation inside a rolled-back transaction.
