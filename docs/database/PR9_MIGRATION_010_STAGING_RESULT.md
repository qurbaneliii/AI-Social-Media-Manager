# PR9 Migration 010 Staging Result

Date: 2026-07-13

Environment type: isolated local PostgreSQL 18 database for PR-only validation

Migration: `aria/db/migrations/010_pr9_backend_alignment.sql`

## Execution Result

- runner: `python -m db.migrate`
- database: isolated `aria_pr9` on `127.0.0.1:55432`
- result: passed permanently
- follow-up rerun: passed duplicate-application guard verification via `[SKIP]` for all previously applied migrations

## Preparation

- created local cluster under `tmp/pr9-pg`
- created schema snapshot before migration at `tmp/pr9-schema-before.sql`
- created required support roles `anon` and `authenticated`
- enabled `uuid-ossp`
- seeded migration history for `001` through `006` because the local PostgreSQL instance does not provide the legacy `vector` extension path used by older migrations

## Verified Schema Outcomes

- `ai_workspaces` present
- `ai_workspace_memberships` present
- `ai_brands` present
- tenant columns added to `ai_brand_memory`, `ai_content_drafts`, `ai_calendar_draft_items`, `ai_community_reply_drafts`, `ai_report_drafts`, and `ai_approval_audit_events`
- `ai_content_variants` present
- tenant foreign keys present for aligned tables
- approval and calendar constraints remained valid
- no unexpected table drops observed

## Post-Migration Live Validation

- backend live PostgreSQL suite: passed
- product runtime flow against the same database: passed after repository and auth-route fixes
- restart persistence against the same database: passed

## Warnings

- the local validation path is PostgreSQL, not a Supabase branch, because the connected Supabase project exposed only its default branch in this session
- `001` and `002` were not replayed from scratch because their historical `pgvector` dependency is unavailable in the local PostgreSQL 18 installation
- this is sufficient evidence for PR-level isolation and permanence, but it is not a substitute for owner-controlled production migration execution

## Rollback Implications

- this migration is treated as one-way schema alignment work
- rollback is not equivalent to successful forward validation
- production rollout should still follow the controlled plan: backup, apply migration, verify schema, deploy backend, deploy frontend, smoke-test
