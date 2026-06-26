# Phase 7 Detail And Review UX Summary

## Phase 7 Summary

Phase 7 hardened the approval-based AI Social Media Manager workflow with safe backend detail DTOs, typed detail routes, request-changes context, audit timeline support, a richer frontend detail review experience, and deployment-facing API/CORS/env checks.

No scraping, publishing, automatic replies, real platform scheduling, social platform integrations, or direct provider calls from new approval UI code were added.

## Pre-Implementation Audit Result

The mandatory pre-implementation audit was completed and documented in `PHASE_7_PRE_IMPLEMENTATION_AUDIT.md`.

Key findings:

- Phase 6 queue DTOs were suitable for list views but not rich enough for detailed review.
- Raw JSONB persistence fields existed in database rows and needed backend-only parsing into safe DTOs.
- Request-changes transitions existed, but frontend review needed reason/change validation and timeline visibility.
- Approval UI used the centralized orchestration API client and did not import direct OpenAI or Anthropic helpers.
- Legacy direct provider helpers still exist for non-approval frontend generation routes.
- Full intended pgvector migration-runner verification remained pending.

## Backend Detail DTOs Added

Added safe schema-first detail DTOs in `aria/apps/llm-orchestration/app/ai/approval/queue.py`:

- `ApprovalAuditTimeline`
- `ContentDraftDetail`
- `CalendarDraftDetail`
- `CommunityReplyDraftDetail`
- `ReportDraftDetail`
- `ApprovalDetail`

The DTO mappers parse persistence JSON internally and expose only curated review fields. They do not expose raw fields such as `content_package_json`, `quality_scores_json`, `calendar_item_json`, `insight_payload_json`, `audit_metadata_json`, or `metadata_json`.

## Backend Detail Routes Added

Added internal detail routes in `aria/apps/llm-orchestration/app/main.py`:

- `GET /internal/ai/approval/detail/content/{draft_id}`
- `GET /internal/ai/approval/detail/calendar/{item_id}`
- `GET /internal/ai/approval/detail/community/{reply_draft_id}`
- `GET /internal/ai/approval/detail/reports/{report_id}`
- `GET /internal/ai/approval/detail/{object_type}/{object_id}`

Route behavior:

- Returns schema-first detail DTOs.
- Includes latest audit events.
- Returns `404` for missing records.
- Returns `400` for invalid generic object types.
- Returns `503` when persistence is unavailable.
- Does not publish, schedule, send, scrape, or call social APIs.

## Revision And Request-Changes Improvements

Request-changes now has a clearer review shape:

- Frontend requires a reason.
- Frontend requires at least one requested change.
- Backend audit events preserve reason, requested changes, reviewer id, reviewer role, timestamp, object type, and object id.
- Detail DTOs expose `last_requested_changes` and `last_review_reason`.
- Audit timeline displays requested changes and reviewer metadata.

Phase 7 does not auto-regenerate content, overwrite the original draft, or introduce a revision table. A richer revision model remains a later phase.

## Frontend Detail UX Added

Updated `aria-frontend/components/approval/ApprovalDashboard.tsx` to load and render safe detail DTOs for selected queue items.

The detail panel now shows:

- Content draft hook, caption, CTA, hashtags, rationale, posting recommendation, visual/video/carousel summaries.
- Calendar item topic, objective, content pillar, content type, and rationale.
- Community original message, suggested reply, sentiment, intent, urgency, confidence, and `auto_reply_allowed=false`.
- Report summary, key insights, and recommendations.
- Approval status, risk/quality summary, model/mock metadata, timestamps, audit timeline, and requested-changes history.
- Loading, action-submitting, validation, network, missing-object, invalid-transition, and persistence-unavailable states through the existing structured error flow.

Safety labels remain visible in review views:

- Approval does not publish.
- Calendar readiness does not schedule to real platforms.
- Community reply approval does not send a reply.
- All AI outputs require human control.

## Frontend API Client Changes

Extended `aria-frontend/lib/api/approval.ts` with detail DTO types and client functions:

- `getApprovalDetail(objectType, objectId)`
- `getContentDraftDetail(draftId)`
- `getCalendarDraftDetail(itemId)`
- `getCommunityReplyDetail(replyDraftId)`
- `getReportDraftDetail(reportId)`
- `requestDraftChanges(...)`

The request-changes payload is typed as `RequestChangesPayload` and includes a required `reason` plus `requested_changes`.

No `any` was introduced in the approval client.

## Direct OpenAI And Anthropic Risk Status

New approval code does not import direct OpenAI or Anthropic helpers.

Still present outside approval workflow:

- `aria-frontend/app/api/ai/_lib.ts` imports OpenAI helpers for legacy AI routes.
- `aria-frontend/lib/openai.ts` constructs a legacy OpenAI client.
- `aria-frontend/app/api/generate/route.ts` imports Anthropic for an existing generation route.

These remain deprecated for new approval workflow work and should be migrated separately after compatibility tests exist.

## Env, CORS, Auth, And Deployment Findings

Frontend:

- Added `NEXT_PUBLIC_AI_ORCHESTRATION_URL` to `aria-frontend/.env.example`.
- Approval API client falls back to `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_API_URL` when the dedicated AI orchestration URL is not set.

Backend:

- Added FastAPI CORS middleware to the LLM orchestration service.
- CORS reads `CORS_ORIGINS` and defaults to local frontend origins for development.

Auth:

- Production auth is not implemented in Phase 7.
- Approval reviewer identity remains explicit placeholder metadata through `reviewer_id` and `reviewer_role`.

## Files Added

- `PHASE_7_PRE_IMPLEMENTATION_AUDIT.md`
- `PHASE_7_DETAIL_AND_REVIEW_UX_SUMMARY.md`
- `aria/apps/llm-orchestration/tests/test_phase_7_approval_detail.py`

## Files Modified

- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `PHASE_4_API_CONTRACTS.md`
- `aria/apps/llm-orchestration/app/ai/approval/queue.py`
- `aria/apps/llm-orchestration/app/main.py`
- `aria-frontend/.env.example`
- `aria-frontend/lib/api/approval.ts`
- `aria-frontend/components/approval/ApprovalDashboard.tsx`

## Backend Tests Run And Results

Command:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests -q -rA
```

Result: passed after fixing Phase 7 route ordering and audit timeline event normalization.

Optional live DB tests were not run because no valid pgvector-enabled `DATABASE_URL` is configured in this environment.

## Frontend Checks Run And Results

Commands:

```powershell
npm.cmd run typecheck
npm.cmd run build
```

Results:

- TypeScript check passed.
- Production build passed.
- `npm.cmd run lint` was not run because the project still lacks a non-interactive ESLint configuration; `next lint` triggers setup.

Safety scans:

- Approval frontend code has no direct OpenAI/Anthropic imports.
- Approval frontend code has no raw persistence JSON field names.
- Forbidden runtime states only appear in safety labels and backend validators that explicitly block publishing/scheduling/sending.
- `auto_reply_allowed` appears only as a safety field and remains false in DTO mapping.

## Bugs Found And Fixed

- Generic detail route originally shadowed type-specific detail routes; route order was corrected.
- Audit timeline originally rejected approval decision objects returned by the fake repository; normalization now accepts both stored audit events and approval decisions.
- Production build timeout during a parallel command was rerun as a clean standalone build and passed.

## What Remains Unverified

- Full `python -m db.migrate` on the intended pgvector Docker stack remains unverified.
- Optional live Postgres approval flow tests still need valid credentials and pgvector support.
- Full browser interaction against a running backend with real queue data remains unverified.
- Production authentication and reviewer identity propagation remain future work.

## Remaining Risks

- Legacy non-approval frontend generation routes still call direct OpenAI/Anthropic helpers.
- Deployment must provide the correct orchestration API URL and CORS origin list.
- Detail DTOs summarize rich structured fields; a future editing/revision UI may need a dedicated revision model instead of audit-only request-changes history.

## Recommended Phase 8

1. Verify the intended pgvector stack with the full migration runner and optional live DB tests.
2. Add production auth/reviewer identity propagation for internal approval routes.
3. Introduce an explicit revision/supersession model if draft editing or regeneration becomes part of the workflow.
4. Migrate legacy frontend provider routes to the centralized LLM orchestration service with compatibility tests.
5. Add observability for approval latency, quality scores, prompt versions, model usage, and reviewer decisions.
