# Supabase Deployment Status

Status: Database setup completed and verified.
Date: 2026-07-08

## Project Status

- Project name: `aria-mvp-demo`
- Project ref: `bypwigurvhlqjhrlgckf`
- Organization: `qurbaneliii's projects`
- Region: `us-east-1`
- Status: `ACTIVE_HEALTHY`
- Supabase URL: `https://bypwigurvhlqjhrlgckf.supabase.co`
- Database host: `db.bypwigurvhlqjhrlgckf.supabase.co`
- PostgreSQL version reported by Supabase: `17.6.1.141`

No existing data was reset or deleted.

## Vector Extension Status

Installed extensions verified:

- `vector` version `0.8.2`
- `pgcrypto` version `1.3`
- `uuid-ossp` version `1.1`

The `vector` extension was enabled before applying the AI table migrations.

## Migrations Applied

Applied migrations:

- `20260708125112 enable_vector_extension`
- `20260708125132 ai_memory_foundation`
- `20260708125204 ai_approval_lifecycle`
- `20260708125254 ai_tables_enable_rls`

The repository migration added by this branch is:

- `aria/db/migrations/009_ai_tables_enable_rls.sql`

## Tables Verified

Verified in the `public` schema:

- `ai_brand_memory`
- `ai_content_drafts`
- `ai_quality_reviews`
- `ai_calendar_draft_items`
- `ai_community_reply_drafts`
- `ai_report_drafts`
- `ai_approval_audit_events`

All seven tables currently report `rls_enabled=true` and `rows=0`.

## Connection Method Used

Database setup used the connected Supabase tool to create the project, run DDL migrations, and inspect tables/extensions.

The backend deployment still needs a backend-only `DATABASE_URL`. The connected Supabase tool did not expose the database password/full connection string, so this value must be copied from the Supabase Dashboard Connect panel into Render only.

## Warnings And Limitations

- RLS is enabled with no public policies on the AI tables. This is intentional for the MVP demo because the browser should not access these tables directly.
- The backend must use a private server-side database connection.
- Do not place the Supabase service role key or database URL in Vercel frontend environment variables.
- Supabase advisors may report informational `rls_enabled_no_policy` notices on these tables. For this backend-only demo, that is acceptable until a proper authenticated API/RLS policy model is designed.
