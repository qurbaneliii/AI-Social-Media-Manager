# Phase 3.5 Database Verification

Date: 2026-06-19

Scope: live/local database verification for the Phase 3 AI persistence foundation.

Not included: frontend work, scraping, publishing, automatic replies, social media integrations, duplicate app-folder cleanup, or deletion of `modified-files-full-code.md`.

## Docker Compose Stack Decision

Two compose files were inspected:

- Root `docker-compose.yml`
- `aria/docker-compose.yml`

For the specific Phase 3.5 verification command:

```powershell
cd aria
$env:DATABASE_URL="postgresql://aria:aria@localhost:5432/aria"
python -m db.migrate
```

the correct stack is `aria/docker-compose.yml`.

Reason:

- `aria/docker-compose.yml` exposes Postgres on host port `5432`.
- It defaults to `POSTGRES_USER=aria`, `POSTGRES_PASSWORD=aria`, and `POSTGRES_DB=aria`.
- It matches the `aria/db/migrate.py` migration runner and the requested `DATABASE_URL`.

The root `docker-compose.yml` is the microservice stack. Its Postgres service uses `postgres/postgres`, does not expose host port `5432` in the inspected file, and therefore does not match the requested host migration command without changes.

No compose file was modified.

## Local Tooling Check

Checked local commands:

- `docker`: not found on PATH.
- Standard Docker Desktop paths checked:
  - `C:\Program Files\Docker\Docker\resources\bin\docker.exe`: not found.
  - `C:\Program Files\Docker\Docker\Docker Desktop.exe`: not found.
- `psql`: not found.
- `pg_isready`: not found.

Because Docker and Postgres CLI tooling are unavailable in this environment, I could not start the correct local Postgres stack from here.

## Migration Verification Result

Migration file:

- `aria/db/migrations/007_ai_memory_foundation.sql`

Static verification:

- Follows repo migration naming convention.
- Uses idempotent `CREATE TABLE IF NOT EXISTS`.
- Uses JSONB for stored schema-first objects and audit metadata.
- Uses `TIMESTAMPTZ NOT NULL DEFAULT now()` timestamps.
- Adds indexes for brand/date lookup paths.
- Uses safe approval status constraints.
- Uses foreign keys from drafts/reviews/calendar items to `ai_brand_memory`.

Live migration attempt:

```powershell
$env:RUN_LIVE_DB_TESTS="1"
$env:DATABASE_URL="postgresql://aria:aria@localhost:5432/aria"
python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
```

Result:

```text
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "aria"
```

A Postgres server is reachable on `localhost:5432`, but it does not accept the expected `aria:aria` credentials. The migration was not applied.

Also tested the root-stack credential shape:

- `postgresql://postgres:postgres@localhost:5432/aria`

Result:

```text
InvalidPasswordError
```

## Tables Verified

Not live-verified because migration could not connect to the local Postgres instance.

The optional live integration test verifies these tables when a valid `DATABASE_URL` is available:

- `ai_brand_memory`
- `ai_content_drafts`
- `ai_quality_reviews`
- `ai_calendar_draft_items`

## Runtime DB Pool Result

Runtime wiring was implemented and unit-tested:

- `aria/apps/llm-orchestration/app/main.py` creates `app.state.db_pool` from `DATABASE_URL` during FastAPI lifespan startup.
- `get_ai_orchestrator(request)` attaches `AIPersistenceRepository` when `app.state.db_pool` exists.
- Mock mode still works when no DB pool is present.

Live runtime DB pool creation was not verified because local Postgres authentication failed.

## Persistence Flow Result

Unit/fake-pool verification passed.

Live persistence flow was not completed because database authentication failed before migrations could run.

The optional live test verifies the complete flow when credentials are correct:

1. Run all migrations through `db.migrate`.
2. Insert a `BrandProfile` into `ai_brand_memory`.
3. Load the stored brand through `BrandMemory`.
4. Generate a mock content package through `AIOrchestrator`.
5. Store the generated package in `ai_content_drafts`.
6. Store the quality review in `ai_quality_reviews`.
7. Generate a mock content calendar.
8. Store draft calendar items in `ai_calendar_draft_items`.
9. Clean up the temporary test brand.

## Tests And Scripts Added

Added optional live DB test:

- `aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py`

It is skipped by default and only runs when both conditions are true:

```powershell
$env:RUN_LIVE_DB_TESTS="1"
$env:DATABASE_URL="postgresql://aria:aria@localhost:5432/aria"
```

This keeps normal unit tests independent of local Postgres.

## Commands Run

Normal test suite:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='.venv\Lib\site-packages;aria/apps/llm-orchestration/app'
python -m pytest aria/apps/llm-orchestration/tests -q
```

Result:

```text
22 passed, 1 skipped
```

Live DB test:

```powershell
$env:RUN_LIVE_DB_TESTS='1'
$env:DATABASE_URL='postgresql://aria:aria@localhost:5432/aria'
python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
```

Result:

```text
FAILED - InvalidPasswordError: password authentication failed for user "aria"
```

## What Remains Unverified

- Applying `007_ai_memory_foundation.sql` to a live local Postgres instance.
- Confirming the four AI persistence tables exist in live Postgres.
- Confirming real runtime DB pool creation against live Postgres.
- Confirming real insert/load/draft/review/calendar persistence against live Postgres.

## Required Next Action Before Phase 4

Start the correct stack or provide a valid `DATABASE_URL`.

Recommended local command when Docker Desktop is installed:

```powershell
cd aria
docker compose up -d postgres
$env:DATABASE_URL="postgresql://aria:aria@localhost:5432/aria"
python -m db.migrate
cd ..
$env:RUN_LIVE_DB_TESTS="1"
$env:PYTHONUTF8="1"
$env:PYTHONPATH=".venv\Lib\site-packages;aria/apps/llm-orchestration/app"
python -m pytest aria/apps/llm-orchestration/tests/test_phase_3_5_live_database.py -q
```

If a Postgres instance is already running on `localhost:5432`, use its actual credentials in `DATABASE_URL` or reset the local volume for the `aria/docker-compose.yml` stack.

## Phase 4 Readiness

Phase 4 is not fully safe to start until the optional live DB test passes against a real Postgres instance.
