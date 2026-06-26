# Phase 6 Frontend Approval Integration Summary

## What Was Implemented

Phase 6 connects the existing dashboard frontend to the Phase 5 internal approval queue and approval lifecycle contracts.

The frontend now provides:

- A typed approval API client that calls the LLM orchestration service.
- Approval queue pages for all drafts, content, calendar, community replies, and reports.
- Filters for brand, platform, and approval status.
- Queue list rows, detail panels, quality/risk summaries, safety labels, and audit history.
- Lifecycle actions for submit, approve, reject, request changes, archive, calendar readiness, and community escalation.
- Clear frontend handling for backend validation, missing-object, invalid-transition, and persistence-unavailable errors.
- A `/approval` redirect to the dashboard approval queue.

All approval behavior remains backend-authoritative. The frontend sends only lifecycle requests and never calls social platform APIs.

## Backend Routes Used

- `GET /internal/ai/approval/queue`
- `GET /internal/ai/approval/queue/content`
- `GET /internal/ai/approval/queue/calendar`
- `GET /internal/ai/approval/queue/community`
- `GET /internal/ai/approval/queue/reports`
- `POST /internal/ai/approval/decision`
- `POST /internal/ai/approval/submit`
- `POST /internal/ai/approval/approve`
- `POST /internal/ai/approval/reject`
- `POST /internal/ai/approval/request-changes`
- `POST /internal/ai/approval/archive`
- `GET /internal/ai/approval/audit/{object_type}/{object_id}`

The frontend uses the Phase 5 queue DTO fields only. It does not render raw persistence JSON fields.

## Safety Guarantees

- Approval does not publish content.
- Calendar `ready_for_scheduling` is an internal readiness status only; it does not schedule to any real platform.
- Community reply drafts remain human-controlled; approval or escalation does not send a reply.
- The approval client has no direct OpenAI, Anthropic, scraping, or social platform API calls.
- Legacy OpenAI helpers remain for existing routes but are marked deprecated for new approval workflow work.

## Files Added

- `PHASE_6_FRONTEND_INTEGRATION_AUDIT.md`
- `PHASE_6_FRONTEND_APPROVAL_INTEGRATION_SUMMARY.md`
- `aria-frontend/lib/api/approval.ts`
- `aria-frontend/components/approval/ApprovalDashboard.tsx`
- `aria-frontend/app/approval/page.tsx`
- `aria-frontend/app/dashboard/approval/page.tsx`
- `aria-frontend/app/dashboard/approval/content/page.tsx`
- `aria-frontend/app/dashboard/approval/calendar/page.tsx`
- `aria-frontend/app/dashboard/approval/community/page.tsx`
- `aria-frontend/app/dashboard/approval/reports/page.tsx`

## Files Modified

- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `aria-frontend/app/api/ai/_lib.ts`
- `aria-frontend/lib/openai.ts`
- `aria-frontend/components/dashboard/Sidebar.tsx`
- `aria-frontend/components/dashboard/TopBar.tsx`
- `aria-frontend/components/dashboard/MobileNav.tsx`
- `aria-frontend/package.json`

The `package.json` postbuild command was made cross-platform with Node so the documented build command runs on Windows. No lockfile changes were made.

## Validation

Backend:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests -q -rA
```

Result: `42 passed, 2 skipped`.

The skipped tests are the optional live Postgres checks, which require `RUN_LIVE_DB_TESTS=1` and a valid `DATABASE_URL`.

Frontend:

```powershell
npm.cmd run typecheck
npm.cmd run build
```

Results:

- TypeScript check passed.
- Production build passed and generated all 37 application routes, including every approval route.
- The rebuilt local server returned `HTTP 200` for `http://localhost:3000/dashboard/approval`.
- `npm.cmd run lint` remains blocked by a pre-existing missing ESLint configuration. Next.js opens its interactive first-run configuration prompt, so no non-interactive lint result exists yet.

## What Remains Unverified

- The intended pgvector Docker stack and the full `python -m db.migrate` migration runner remain unverified in this environment.
- The optional live Postgres approval tests need valid database credentials and the intended extension-enabled database.
- Full browser interaction against a running frontend and live LLM orchestration service still needs a configured service URL and database-backed queue data. The local route itself was verified over HTTP.
- Existing direct provider-backed frontend generation helpers are not migrated in Phase 6; only their use for new approval work is deprecated.

## Risks

- A user without access to the internal orchestration endpoint will see a structured API error in the approval queue rather than draft data.
- The frontend uses local/session storage token conventions already present in the project; final authentication integration should confirm the production token key and CORS policy.
- Detail views intentionally show queue DTO previews and summaries. A richer draft-editing experience may need backend detail DTOs rather than exposing persistence internals.

## Recommended Phase 7

1. Verify the intended pgvector Docker/Postgres stack with `python -m db.migrate` and run optional live tests.
2. Add authenticated deployment configuration and CORS validation for the orchestration API.
3. Add backend detail DTO endpoints for safe full-draft review and revision workflows.
4. Migrate legacy direct frontend provider routes to the centralized LLM orchestration service in a separate, compatibility-tested phase.
