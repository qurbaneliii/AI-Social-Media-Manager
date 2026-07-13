# PR #9 Production Merge Readiness

Date: 2026-07-13

Branch: `codex/aria-final-ui-ux-redesign`

Starting SHA: `36208adfeb89c694c65339ab70ea1f97a83343be`

PR: `https://github.com/qurbaneliii/AI-Social-Media-Manager/pull/9`

Status: `PARTIALLY COMPLETED - NOT READY TO MERGE`

## Isolated Database

- Environment: local PostgreSQL 18 cluster created under `tmp/pr9-pg`
- Port: `55432`
- Database: isolated PR-only `aria_pr9`
- Production database usage: none
- Supabase production branch usage: none

## Migration 010

- Migration file: `aria/db/migrations/010_pr9_backend_alignment.sql`
- Permanent isolated application: passed
- Migration runner duplicate protection: verified on rerun, all migrations skipped
- Pre-migration schema snapshot: `tmp/pr9-schema-before.sql`

## Live Database Verification

- Backend Ruff: passed
- Backend pytest with `RUN_LIVE_DB_TESTS=1`: passed
- Result: `68 passed, 0 failed, 0 skipped`
- Previously credential-gated live suites now executed against the isolated database

## Persistent Non-Preview E2E

Verified against:

- backend: `uvicorn main:app --host 127.0.0.1 --port 8010`
- frontend: production `next start -p 3201`
- mode: `NEXT_PUBLIC_PREVIEW_MODE=false`
- AI mode: explicit backend mock mode only

Verified flow:

1. registered and authenticated a real local test user against frontend auth routes
2. resolved workspace and active brand
3. saved a complete Brand Brain profile
4. generated persisted mock-labelled content through `/v1/posts/generate`
5. saved an additional manual draft through `/v1/posts/drafts`
6. submitted generated content for approval
7. approved the generated content
8. verified trusted audit actor identity
9. created an internal calendar item linked to the approved content draft
10. verified Overview, Insights, Capabilities, Content, Approval, and Calendar API responses
11. restarted the backend process
12. reloaded the same post, audit trail, calendar item, Overview, and Insights successfully

Machine-readable evidence: [docs/release/evidence/pr9-persistent-e2e.json](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/release/evidence/pr9-persistent-e2e.json)

## Browser Verification

Production browser verification succeeded for:

- `/dashboard/brand`
- `/dashboard/brand-brain`
- `/posts/new`
- `/posts`
- `/dashboard/approval`
- `/scheduler`
- `/analytics`
- `/dashboard/settings`

Checks:

- authenticated non-preview session
- one shared `ProductShell`
- one `<main>`
- no console errors
- no page errors
- no HTTP 4xx/5xx responses during the final route pass

Desktop screenshots:

- [overview](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/overview-desktop-light.png)
- [brand-brain](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/brand-brain-desktop-light.png)
- [create](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/create-desktop-light.png)
- [content](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/content-desktop-light.png)
- [approval](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/approval-desktop-light.png)
- [calendar](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/calendar-desktop-light.png)
- [insights](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/insights-desktop-light.png)
- [settings](/C:/Users/qurba/Documents/Codex/2026-07-11/new-chat/work/AI-Social-Media-Manager/docs/product/screenshots/pr9-persistent-e2e/settings-desktop-light.png)

## Deployment Checks

- Canonical Vercel project: `ai-social-media-manager-gl7x`
- Canonical Vercel deployment status for starting SHA: success
- Stale Vercel project: `ai-social-media-manager`
- Stale Vercel deployment status for starting SHA: failure
- Netlify deploy-preview status for starting SHA: failure

The available Vercel and GitHub connectors in this session allowed inspection, but not project-settings mutation or Netlify integration removal. Those checks remain unresolved blockers.

## Remaining Blockers

1. stale Vercel project `ai-social-media-manager` still reports failure on the PR
2. Netlify `deploy-preview` still reports failure on the PR
3. PR body still needs the new evidence pasted in
4. PR must remain draft until obsolete required checks are disconnected or corrected by the repository owner or a tool with settings-write access
