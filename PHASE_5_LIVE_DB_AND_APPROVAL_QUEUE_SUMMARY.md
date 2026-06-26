# Phase 5 Live DB And Approval Queue Summary

## Gate Check Result

Reviewed:

- `PHASE_3_IMPLEMENTATION_SUMMARY.md`
- `PHASE_3_5_DATABASE_VERIFICATION.md`
- `PHASE_4_IMPLEMENTATION_SUMMARY.md`
- `PHASE_4_API_CONTRACTS.md`
- `AI_ARCHITECTURE.md`
- migrations `007` and `008`
- `aria/db/migrate.py`
- `aria/docker-compose.yml`
- root `docker-compose.yml`
- `aria/apps/llm-orchestration/app/main.py`
- `aria/apps/llm-orchestration/app/ai/persistence/repository.py`
- `aria/apps/llm-orchestration/app/ai/approval/service.py`

Ready:

- Phase 3/4 code paths exist and are test-covered.
- Runtime DB pool wiring exists through FastAPI lifespan and `DATABASE_URL`.
- `AIPersistenceRepository` is attached to `AIOrchestrator` when a pool exists.
- Approval lifecycle routes, service, and repository methods exist.

Still unverified at gate:

- Live application of migrations `007` and `008`.
- Real asyncpg persistence against a live database.
- Full migration runner execution in the local environment.

Required changes found:

- Calendar draft persistence passed ISO strings to asyncpg date/time parameters. Live testing caught this and the repository now passes Python `date` and `time` objects directly.
- Raw draft listing responses needed stable queue DTOs before frontend approval queue work.

## Database Stack Decision

The correct intended local stack remains `aria/docker-compose.yml` because it exposes Postgres at `localhost:5432` with expected credentials:

```text
postgresql://aria:aria@localhost:5432/aria
```

Docker is not available in this environment:

- `docker` not found on PATH.
- `C:\Program Files\Docker\Docker\resources\bin\docker.exe` not found.

A local Postgres server is already listening on `5432`, but it rejects both expected credential pairs:

- `aria:aria`
- `postgres:postgres`

No existing database volume or service was reset or modified.

For safe verification, a separate temporary Postgres 18 cluster was created on `localhost:5433` using installed local PostgreSQL binaries and a temp data directory. It used:

```text
postgresql://aria:aria@localhost:5433/aria
```

The temporary cluster was stopped after verification.

## Migration Verification Result

Full repo migration runner:

```powershell
cd aria
$env:DATABASE_URL="postgresql://aria:aria@localhost:5433/aria"
python -m db.migrate
```

Result:

```text
FeatureNotSupportedError: extension "vector" is not available
```

Reason: the temporary DB is plain PostgreSQL, while earlier migration `001_schema.sql` requires `CREATE EXTENSION vector`. The intended Docker image in `aria/docker-compose.yml` is `pgvector/pgvector:pg16`; Docker was unavailable, so the full runner could not be proven end to end.

AI migrations verified directly against real Postgres:

```powershell
psql -h localhost -p 5433 -U aria -d aria -f 007_ai_memory_foundation.sql -f 008_ai_approval_lifecycle.sql
```

Result:

```text
007_ai_memory_foundation.sql applied
008_ai_approval_lifecycle.sql applied
```

## Tables Verified

Verified in real Postgres on the temporary `5433` database:

- `ai_brand_memory`
- `ai_content_drafts`
- `ai_quality_reviews`
- `ai_calendar_draft_items`
- `ai_community_reply_drafts`
- `ai_report_drafts`
- `ai_approval_audit_events`

Verified constraints/indexes included:

- `ai_community_reply_drafts_auto_reply_allowed_check`
- content/calendar/community/report approval status checks
- quality review `review_status` check
- indexes for brand/status/created queue reads
- audit index on `object_type`, `object_id`, `created_at`

`schema_migrations` exists from the failed runner attempt but is empty because the full runner stopped before completing migration `001`.

## Runtime DB Pool Verification Result

Normal tests verify:

- FastAPI lifespan creates `app.state.db_pool` when `DATABASE_URL` is configured.
- `get_ai_orchestrator(request)` attaches `AIPersistenceRepository`.
- Persistence routes return `503` when no DB pool exists.
- Mock mode still works with persistence disabled.

The live Phase 5 test verifies real asyncpg repository operations against Postgres.

## Real Persistence Flow Result

Passed in optional live test against `postgresql://aria:aria@localhost:5433/aria`:

- Inserted a realistic `BrandProfile` into `ai_brand_memory`.
- Loaded that brand through `BrandMemory`.
- Generated a mock content package through `AIOrchestrator`.
- Stored generated content in `ai_content_drafts`.
- Stored quality review in `ai_quality_reviews`.
- Generated a mock content calendar.
- Stored calendar draft items in `ai_calendar_draft_items`.
- Analyzed a mock community message.
- Stored suggested reply in `ai_community_reply_drafts`.
- Verified `auto_reply_allowed=false`.
- Stored a report draft in `ai_report_drafts`.
- Submitted and approved a content draft.
- Submitted, approved, and marked a calendar item `ready_for_scheduling`.
- Submitted and approved a community reply draft.
- Stored and listed approval audit events.
- Verified no object became published, scheduled on a platform, or sent.

## Approval Queue DTOs Added

Added schema-first queue DTOs in `aria/apps/llm-orchestration/app/ai/approval/queue.py`:

- `DraftListFilters`
- `ApprovalQueueItem`
- `ContentDraftQueueItem`
- `CalendarDraftQueueItem`
- `CommunityReplyQueueItem`
- `ReportDraftQueueItem`
- `ApprovalQueueResponse`
- `ContentApprovalQueueResponse`
- `CalendarApprovalQueueResponse`
- `CommunityApprovalQueueResponse`
- `ReportApprovalQueueResponse`
- `ApprovalAuditEventResponse`

DTOs expose frontend-safe preview fields and do not expose raw database JSON blobs.

## Approval Queue Routes Added

- `GET /internal/ai/approval/queue`
- `GET /internal/ai/approval/queue/content`
- `GET /internal/ai/approval/queue/calendar`
- `GET /internal/ai/approval/queue/community`
- `GET /internal/ai/approval/queue/reports`

Existing Phase 4 routes remain:

- `GET /internal/ai/drafts/content`
- `GET /internal/ai/drafts/calendar`
- `GET /internal/ai/drafts/community`
- `GET /internal/ai/approval/audit/{object_type}/{object_id}`

Supported queue filters:

- `brand_id`
- `status`
- `object_type`
- `platform`
- `limit`
- `offset`
- `created_after`
- `created_before`

Invalid object/status combinations return `400`. Missing persistence returns `503`.

## Files Added

- `PHASE_5_LIVE_DB_AND_APPROVAL_QUEUE_SUMMARY.md`
- `aria/apps/llm-orchestration/app/ai/approval/queue.py`
- `aria/apps/llm-orchestration/tests/test_phase_5_approval_queue.py`
- `aria/apps/llm-orchestration/tests/test_phase_5_live_database_approval_flow.py`

## Files Modified

- `AI_ARCHITECTURE.md`
- `AI_ARCHITECTURE_AUDIT.md`
- `PHASE_4_API_CONTRACTS.md`
- `aria/apps/llm-orchestration/app/main.py`
- `aria/apps/llm-orchestration/app/ai/persistence/repository.py`
- `aria/apps/llm-orchestration/tests/test_phase_4_approval.py`

## Tests Run

Normal suite:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests -q -rA
```

Result:

```text
42 passed, 2 skipped
```

Phase 5 live DB test:

```powershell
$env:RUN_LIVE_DB_TESTS='1'
$env:DATABASE_URL='postgresql://aria:aria@localhost:5433/aria'
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests/test_phase_5_live_database_approval_flow.py -q -rA
```

Result:

```text
1 passed
```

Older full-runner live DB test:

```powershell
$env:RUN_LIVE_DB_TESTS='1'
$env:DATABASE_URL='postgresql://aria:aria@localhost:5433/aria'
python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
```

Result:

```text
FAILED - FeatureNotSupportedError: extension "vector" is not available
```

This is expected for the temporary plain Postgres cluster and remains unverified until the intended pgvector Docker stack is available.

## What Remains Unverified

- Full `python -m db.migrate` success on the intended `pgvector/pgvector` Docker stack.
- Local `localhost:5432` stack with expected `aria:aria` credentials.
- `schema_migrations` populated by a successful full migration run.
- Long-running deployed FastAPI service behavior with a real database pool.

## Risks

- Existing local Postgres on `5432` uses unknown credentials.
- Plain PostgreSQL cannot run the full repo migration chain because pgvector is required before migration `007`.
- Queue DTOs are stable enough for frontend planning, but detail endpoints may still be needed before rich approval UI work.

## Recommended Phase 6

Phase 6 can begin backend-to-frontend approval queue integration only after choosing one of these paths:

1. Start the intended `aria/docker-compose.yml` pgvector Postgres stack with valid credentials and run `python -m db.migrate`.
2. Provide the valid `DATABASE_URL` for the existing local `5432` Postgres instance if it already has pgvector.

Once that is done, run both optional live tests and then build frontend approval queues against the Phase 5 DTO routes. Continue to avoid scraping, publishing, automatic replies, and real platform scheduling.
