# Manual Deployment Bridge Status

Date: 2026-07-08
Repository: `qurbaneliii/AI-Social-Media-Manager`
Branch: `deploy/mvp-vercel-render-supabase`
PR: `https://github.com/qurbaneliii/AI-Social-Media-Manager/pull/7`

## Purpose

This bridge tracks the remaining provider-side steps that could not be completed by connected tools. It is intentionally not a success report for the deployed MVP. The MVP is only fully deployed after Render, Vercel, and Supabase are connected and verified with live URLs.

## Completed Automatically

- GitHub branch and PR were verified.
- Local branch was confirmed to match `origin/deploy/mvp-vercel-render-supabase`.
- Deployment docs and provider config files were inspected.
- Supabase project `aria-mvp-demo` was verified as `ACTIVE_HEALTHY`.
- Supabase `vector` extension was verified at version `0.8.2`.
- Supabase migrations were verified:
  - `20260708125112 enable_vector_extension`
  - `20260708125132 ai_memory_foundation`
  - `20260708125204 ai_approval_lifecycle`
  - `20260708125254 ai_tables_enable_rls`
- Required AI tables were verified with RLS enabled and zero rows:
  - `public.ai_brand_memory`
  - `public.ai_content_drafts`
  - `public.ai_quality_reviews`
  - `public.ai_calendar_draft_items`
  - `public.ai_community_reply_drafts`
  - `public.ai_report_drafts`
  - `public.ai_approval_audit_events`
- Vercel existing project deployments were inspected.
- Render tool and local CLI availability were checked.
- Backend tests were rerun in mock mode: `50 passed`, `2 skipped`.
- Frontend `npm run typecheck` was rerun and passed.
- Frontend `npm run build` was rerun and passed, generating the target dashboard routes.

## Blocked

### Supabase Secret Access

`BLOCKED_SECRET_REQUIRED: Supabase DATABASE_URL is not accessible through connected tools. User must manually copy the backend-only connection string from Supabase Dashboard -> Connect and paste it into Render environment variables.`

Why blocked:

- The connected Supabase tools expose project status, extensions, migrations, tables, advisors, API URL, and publishable keys.
- They do not expose the database password or full server-side PostgreSQL connection string.
- The connection string must not be invented, reconstructed without the password, committed, or placed in Vercel frontend env vars.

Exact user input needed:

- Backend-only Supabase PostgreSQL connection string from Supabase Dashboard -> Connect.
- Use the real DB password in the string.
- Prefer a pooled connection string suitable for a hosted backend if available; a direct connection is acceptable for this free MVP if Render can reach it.

How to verify after manual step:

- Render environment contains `DATABASE_URL`.
- The value is not visible in Git, Vercel public env vars, docs, or frontend code.
- Render backend starts and can query Supabase-backed routes without database connection errors.

### Render Tool Access

`BLOCKED_RENDER_TOOL_ACCESS: Render service creation/configuration/log access is not available through connected tools. User must manually create/configure Render Web Service.`

Why blocked:

- Tool discovery did not expose Render service creation, env-var, deploy, log, workspace, or status tools.
- `render` CLI is not installed locally.
- `RENDER_API_KEY` is not present in the local environment.
- `DATABASE_URL` is not available to set on the service.

Exact user input/action needed:

- Create Render Web Service `aria-ai-orchestration-mvp`.
- Connect repo `qurbaneliii/AI-Social-Media-Manager`.
- Select branch `deploy/mvp-vercel-render-supabase`.
- Set root directory `aria/apps/llm-orchestration`.
- Set build command `pip install -U pip && pip install -e .`.
- Set start command `PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Set the backend env vars listed in `DEPLOYMENT_ENV_VARS.md`.

How to verify after manual step:

- Render service status is live.
- Render logs show Uvicorn startup and no missing env-var crash.
- These routes return HTTP 200 or structured JSON:
  - `/health`
  - `/docs`
  - `/openapi.json`
  - `/internal/ai/workspace-context`

### Vercel Tool Access

`BLOCKED_VERCEL_TOOL_ACCESS: Vercel project/root-directory/env-var write operations are not available through connected tools. User must manually create/update Vercel project.`

Why blocked:

- Vercel tools can inspect projects, deployments, build logs, and deployment URLs.
- No tool was exposed to create the requested project, update root directory, or set environment variables.
- The Render backend URL does not exist yet, so `NEXT_PUBLIC_AI_ORCHESTRATION_URL` cannot be finalized.

Latest Vercel evidence:

- Project `ai-social-media-manager` latest branch deployment `dpl_HX572bRLdsQcgf5T1k7TFZLVJKEZ` failed because the configured root directory `mainn` does not exist.
- Project `ai-social-media-manager-gl7x` latest branch deployment `dpl_3boLrFXUQs41un26ojfQ8nTXioyH` is `READY`, but build logs show no app files were prepared.
- Neither existing project is a verified deployment of the `aria-frontend` Next.js app.

Exact user input/action needed:

- Create or update Vercel project `aria-ai-social-media-manager-mvp`.
- Connect repo `qurbaneliii/AI-Social-Media-Manager`.
- Select branch `deploy/mvp-vercel-render-supabase`.
- Set root directory `aria-frontend`.
- Set framework `Next.js`.
- Set install command `npm install` or `npm ci`.
- Set build command `npm run build`.
- Set `NEXT_PUBLIC_AI_ORCHESTRATION_URL` to the Render backend URL after Render is live.

How to verify after manual step:

- Vercel production deployment is ready.
- Build logs show Next.js build output from `aria-frontend`.
- Dashboard pages load from the production URL:
  - `/dashboard/ai`
  - `/dashboard/brand-brain`
  - `/dashboard/content-studio`
  - `/dashboard/approval`

## Manual Order Of Operations

1. Copy the Supabase backend PostgreSQL connection string from Supabase Dashboard -> Connect.
2. Create the Render backend and paste the connection string only into Render `DATABASE_URL`.
3. Deploy Render and copy the Render backend URL.
4. Create or update the Vercel frontend project rooted at `aria-frontend`.
5. Set Vercel `NEXT_PUBLIC_AI_ORCHESTRATION_URL` to the Render backend URL.
6. Deploy Vercel and copy the Vercel production URL.
7. Replace temporary Render `CORS_ORIGINS` with the exact Vercel production URL.
8. Redeploy Render.
9. Verify frontend-to-backend calls from the Vercel production site.

## Not Production-Ready Yet

- No live Render backend URL is verified.
- No live Vercel production frontend URL is verified.
- Final CORS is not configured.
- End-to-end deployed dashboard flows are not verified.
- The AI tables have RLS enabled but no public policies, which is intentional for this backend-only demo and not a production authorization model.
- Production auth, tenant isolation, observability, rate limiting, backup/restore, and secret rotation are still required.
