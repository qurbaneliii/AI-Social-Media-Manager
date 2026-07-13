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

`aria/db/migrations/010_pr9_backend_alignment.sql` was applied permanently to an isolated PostgreSQL 18 database created for PR #9 under `tmp/pr9-pg`.

Verification steps completed:

- pre-migration schema snapshot captured at `tmp/pr9-schema-before.sql`
- migration runner applied `007`, `008`, `009`, and `010` successfully on the isolated database
- rerun confirmed duplicate-application guard behavior with `[SKIP]` for all previously applied migrations
- live backend suite executed against the same isolated database with no live-test skips
- product runtime persistence flow and backend-restart persistence were both verified against the same database

## Verification Results

| Command | Result |
| --- | --- |
| `python -m ruff check aria/apps/llm-orchestration/app aria/apps/llm-orchestration/tests` | Passed |
| `python -m pytest aria/apps/llm-orchestration/tests -q -rA` with live DB env | Passed; `68 passed, 0 failed, 0 skipped` |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed |
| `npm test` | Passed; 5 tests |
| `npm run contracts:generate` | Passed |
| `npm audit --omit=dev` | Passed; 0 runtime vulnerabilities |
| `npm run build` | Passed; exit 0; Next 15.5.20 compiled successfully with dynamic post detail routes |
| Persistent non-preview browser route pass | Passed on eight canonical routes; one shell marker and one main landmark on each |

Additional fixes made during live verification:

- `ProductRepository.create_content` now writes truthful non-null draft `model` values for both mock-generated and user-authored content
- frontend registration now creates workspace, membership, and brand rows explicitly
- the legacy persistence adapter no longer overwrites correct `workspace_id` values with legacy `brand_id` fallbacks
- approval audit events now normalize UUID fields before Pydantic validation
