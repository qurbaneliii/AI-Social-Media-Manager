# Deployment Readiness Audit

Repository: `qurbaneliii/AI-Social-Media-Manager`
Branch: `deploy/mvp-vercel-render-supabase`
Audit date: 2026-07-08

## Summary

The repo contains a deployable MVP shape for ARIA's AI workspace:

- Frontend: Next.js app in `aria-frontend`.
- Backend: FastAPI LLM orchestration service in `aria/apps/llm-orchestration`.
- Database: PostgreSQL with Supabase-hosted `pgvector` support.
- MVP mode: mock AI enabled with `AI_MOCK_MODE=true`; no paid OpenAI call is required for the first demo deploy.

The Supabase database was created and the MVP AI migrations were applied. Local backend and frontend checks pass after adding a Prisma generate prebuild step. Render and Vercel live deployment could not be completed from this session because Render write access/API auth was not available, Vercel CLI auth was not available, and the Supabase database password/full backend `DATABASE_URL` is not exposed by the connected Supabase tool.

## Frontend Entrypoint

- Root directory: `aria-frontend`
- Framework: Next.js
- Main app entrypoint: `aria-frontend/app/page.tsx`
- Dashboard layout: `aria-frontend/app/dashboard/layout.tsx`
- Target dashboard routes:
  - `/dashboard/ai`
  - `/dashboard/brand-brain`
  - `/dashboard/content-studio`
  - `/dashboard/strategy`
  - `/dashboard/ai-analyst`
  - `/dashboard/calendar-ai`
  - `/dashboard/community-ai`
  - `/dashboard/reports-ai`
  - `/dashboard/approval`
- Backend client config:
  - `aria-frontend/lib/api/ai-workspace.ts`
  - `aria-frontend/lib/api/approval.ts`
  - Uses `NEXT_PUBLIC_AI_ORCHESTRATION_URL`, falling back to `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_API_URL`.

## Backend Entrypoint

- Service directory: `aria/apps/llm-orchestration`
- FastAPI app: `aria/apps/llm-orchestration/app/main.py`
- FastAPI variable: `app`
- Local/deploy start command:

```bash
PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT
```

Important backend routes found in code:

- `GET /health`
- `GET /openapi.json`
- `GET /docs`
- `GET /internal/ai/workspace-context`
- `GET /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile`
- `PUT /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile/validate`
- `POST /internal/ai/generate-content-package`
- `POST /internal/ai/brand-strategy`
- `POST /internal/ai/content-calendar`
- `POST /internal/ai/community/analyze`
- `POST /internal/ai/reports/insights`
- `POST /internal/ai/content-quality/review`
- `POST /internal/ai/approval/decision`
- `POST /internal/ai/approval/submit`
- `POST /internal/ai/approval/approve`
- `POST /internal/ai/approval/reject`
- `POST /internal/ai/approval/request-changes`
- `POST /internal/ai/approval/archive`
- Approval queue/detail/audit routes under `/internal/ai/approval/*`

## Database Requirements

- PostgreSQL
- Supabase project for MVP demo
- Required extensions:
  - `vector`
  - `pgcrypto`
  - `uuid-ossp`
- Required tables:
  - `ai_brand_memory`
  - `ai_content_drafts`
  - `ai_quality_reviews`
  - `ai_calendar_draft_items`
  - `ai_community_reply_drafts`
  - `ai_report_drafts`
  - `ai_approval_audit_events`

## Migration Requirements

MVP-required migrations:

- `enable_vector_extension`
- `aria/db/migrations/007_ai_memory_foundation.sql`
- `aria/db/migrations/008_ai_approval_lifecycle.sql`
- `aria/db/migrations/009_ai_tables_enable_rls.sql`

Earlier migrations in `aria/db/migrations/001` through `006` are broader local-platform infrastructure migrations. The LLM orchestration MVP persistence repository uses the AI tables from migrations `007` and `008`.

## Environment Variables Needed

Backend on Render:

- `DATABASE_URL`
- `AI_MOCK_MODE=true`
- `OPENAI_API_KEY=replace-me`
- `OPENAI_MODEL=gpt-4o-mini`
- `AI_TEMPERATURE=0.4`
- `AI_MAX_RETRIES=2`
- `AI_REQUEST_TIMEOUT_SECONDS=30`
- `CORS_ORIGINS=<Vercel production URL>`

Frontend on Vercel:

- `NEXT_PUBLIC_AI_ORCHESTRATION_URL=<Render backend URL>`
- Optional safe public values:
  - `NEXT_PUBLIC_API_BASE_URL=<Render backend URL>`
  - `NEXT_PUBLIC_API_URL=<Render backend URL>`
  - `NEXT_PUBLIC_PREVIEW_MODE=true`
  - `NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS=45000`
  - `NEXT_PUBLIC_AI_REQUEST_RETRIES=2`

Do not configure backend secrets in Vercel public environment variables.

## Build Commands

Frontend:

```bash
cd aria-frontend
npm ci
npm run typecheck
npm run build
```

Backend test command from repo root:

```bash
PYTHONPATH=aria/apps/llm-orchestration/app AI_MOCK_MODE=true OPENAI_API_KEY=replace-me python -m pytest aria/apps/llm-orchestration/tests -q -rA
```

Render backend build command:

```bash
pip install --upgrade pip && pip install -e .
```

## Start Commands

Backend:

```bash
PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT
```

Frontend:

Vercel Next.js default runtime after `npm run build`.

## Deployment Blockers

1. Render write access is not available in this Codex session.
   - No Render MCP/app deployment tool was exposed.
   - `render` CLI is not installed locally.
   - No `RENDER_API_KEY` environment variable is present.

2. Backend `DATABASE_URL` cannot be constructed safely from the connected Supabase tool alone.
   - The Supabase project was created and verified.
   - The database password/full pooled connection string was not exposed to Codex.
   - This value must be copied from Supabase Dashboard Connect settings into Render only.

3. Vercel CLI auth is not available locally.
   - `npx vercel@latest whoami` did not complete as an authenticated non-interactive command.
   - The connected Vercel tool can inspect projects, but no environment-variable write tool was exposed.

4. Existing Vercel projects are not a verified deployment of this branch.
   - `ai-social-media-manager` latest production deployment is `ERROR`.
   - `ai-social-media-manager-gl7x` has a ready deployment record, but the live root and `/dashboard/ai` returned Vercel `404`.

## Exact Fixes Needed Before Deploy

Completed in this branch:

- Added `prebuild` script to run `prisma generate` before Next build.
- Added `aria/db/migrations/009_ai_tables_enable_rls.sql`.
- Added `render.yaml` for a Render free web service.
- Added `aria-frontend/vercel.json` with Next.js build settings.

Still needed outside the repo:

- Create/import the Render web service using `render.yaml`.
- Set Render `DATABASE_URL` from Supabase Dashboard.
- Set Render `CORS_ORIGINS` after the final Vercel URL is known.
- Configure Vercel root directory as `aria-frontend`.
- Set Vercel `NEXT_PUBLIC_AI_ORCHESTRATION_URL` to the Render URL.
- Redeploy both services and verify end-to-end dashboard calls.
