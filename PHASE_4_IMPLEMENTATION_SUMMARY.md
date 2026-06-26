# Phase 4 Implementation Summary

## What Was Implemented

Phase 4 adds a backend-only approval lifecycle for AI-generated drafts:

- Central approval schemas, statuses, actions, decisions, audit events, and draft record models.
- Explicit transition validation for content drafts, calendar draft items, community reply drafts, and report drafts.
- Approval service that validates transitions, updates draft records, writes audit events, and returns schema-first results.
- Persistence repository methods for draft lookup, approval status updates, community reply draft storage, approval audit storage/listing, and draft listing.
- Internal `/internal/ai/...` approval and draft-listing routes.
- Community message analysis now persists suggested replies as community reply drafts when persistence is enabled.
- New migration for approval lifecycle tables, constraints, indexes, community reply drafts, report drafts, and approval audit events.

No frontend UI, scraping, publishing, automatic replies, platform scheduling, or social media integrations were added.

## Gate Check From Phase 3.5

Phase 3.5 live database verification was attempted before Phase 4. Local Postgres authentication failed with `InvalidPasswordError`, so live DB migration/runtime persistence remains unverified.

Code-level Phase 3 readiness was sufficient to proceed:

- `app.state.db_pool` runtime wiring exists.
- `AIPersistenceRepository` is attached to `AIOrchestrator` when a DB pool exists.
- Optional live DB test exists and is skipped unless explicitly enabled.
- Normal fake-pool/unit verification passes.

Phase 4 should not be reported as live-Postgres verified until valid local DB credentials are provided and the optional live test passes.

## Files Added

- `PHASE_4_API_CONTRACTS.md`
- `PHASE_4_IMPLEMENTATION_SUMMARY.md`
- `aria/apps/llm-orchestration/app/ai/approval/__init__.py`
- `aria/apps/llm-orchestration/app/ai/approval/errors.py`
- `aria/apps/llm-orchestration/app/ai/approval/schemas.py`
- `aria/apps/llm-orchestration/app/ai/approval/service.py`
- `aria/apps/llm-orchestration/app/ai/approval/transitions.py`
- `aria/apps/llm-orchestration/tests/test_phase_4_approval.py`
- `aria/db/migrations/008_ai_approval_lifecycle.sql`

## Files Modified

- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `aria/apps/llm-orchestration/app/ai/persistence/repository.py`
- `aria/apps/llm-orchestration/app/main.py`

## Migration Added

`aria/db/migrations/008_ai_approval_lifecycle.sql`

Migration scope:

- Maps older content draft statuses into the Phase 4 lifecycle.
- Adds lifecycle status constraints and indexes for content drafts.
- Adds `review_status` for quality reviews.
- Adds `approval_status` for calendar draft items.
- Creates `ai_community_reply_drafts`.
- Creates `ai_report_drafts`.
- Creates `ai_approval_audit_events`.
- Enforces `auto_reply_allowed=false` for community reply drafts.

Live application of this migration is not verified yet because local Postgres authentication failed during Phase 3.5.

## API Routes Added

- `POST /internal/ai/approval/decision`
- `POST /internal/ai/approval/submit`
- `POST /internal/ai/approval/approve`
- `POST /internal/ai/approval/reject`
- `POST /internal/ai/approval/request-changes`
- `POST /internal/ai/approval/archive`
- `GET /internal/ai/approval/audit/{object_type}/{object_id}`
- `GET /internal/ai/drafts/content`
- `GET /internal/ai/drafts/calendar`
- `GET /internal/ai/drafts/community`

## Approval Lifecycle Rules

Content drafts:

- `draft -> in_review`
- `draft -> approved`
- `draft -> rejected`
- `draft -> changes_requested`
- `in_review -> approved`
- `in_review -> rejected`
- `in_review -> changes_requested`
- `changes_requested -> draft`
- `approved -> archived`
- `rejected -> archived`

Calendar draft items:

- `draft -> in_review`
- `in_review -> approved`
- `in_review -> rejected`
- `in_review -> changes_requested`
- `approved -> ready_for_scheduling`
- `ready_for_scheduling -> archived`
- `rejected -> archived`
- `changes_requested -> draft`

Community reply drafts:

- `draft -> in_review`
- `in_review -> approved`
- `in_review -> rejected`
- `in_review -> escalated`
- `in_review -> changes_requested`
- `changes_requested -> draft`
- `approved -> archived`
- `rejected -> archived`
- `escalated -> archived`

Report drafts:

- `draft -> in_review`
- `draft -> approved`
- `draft -> rejected`
- `draft -> changes_requested`
- `in_review -> approved`
- `in_review -> rejected`
- `in_review -> changes_requested`
- `changes_requested -> draft`
- `approved -> archived`
- `rejected -> archived`

No transition can create `published`, `scheduled`, or `sent`.

## Tests Run

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests -q
```

Result:

```text
37 passed, 1 skipped
```

The skipped test is the optional live database verification path, which requires `RUN_LIVE_DB_TESTS=1` and a valid `DATABASE_URL`.

## What Remains Unverified

- Live application of migrations `007_ai_memory_foundation.sql` and `008_ai_approval_lifecycle.sql`.
- Live runtime persistence through a real asyncpg pool.
- Optional live DB test with valid `DATABASE_URL`.
- Deployment-time behavior when the orchestration service starts with a real database.

## Risks

- If a database has already applied `007_ai_memory_foundation.sql`, `008_ai_approval_lifecycle.sql` must be applied before routes that write community reply drafts or approval audit events are used.
- Existing database rows with old Phase 3 content approval values are mapped by the migration, but this still needs live DB verification.
- Draft listing routes return raw persisted records; Phase 5 can add narrower read DTOs if frontend consumers need a more stable presentation contract.

## Recommended Phase 5

Before frontend work, complete live DB verification with valid credentials:

1. Apply migrations through `python -m db.migrate`.
2. Run the optional live database test with `RUN_LIVE_DB_TESTS=1`.
3. Verify approval routes against live persisted rows.
4. Add read DTOs for approval queues if frontend integration is next.
5. Continue to avoid scraping, publishing, auto-replies, and real platform scheduling until the approval queue is proven end to end.
