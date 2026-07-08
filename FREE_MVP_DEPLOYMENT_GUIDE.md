# Free MVP Deployment Guide

This guide deploys ARIA as a demo/free-tier MVP:

- Frontend: Vercel, Next.js, root `aria-frontend`
- Backend: Render, FastAPI, root `aria/apps/llm-orchestration`
- Database: Supabase PostgreSQL with `vector`
- AI mode: `AI_MOCK_MODE=true`
- No scraping, no auto-publishing, no auto-replies, no real scheduling

## Current Verified State

Completed:

- Supabase project `aria-mvp-demo` created.
- Supabase project ref `bypwigurvhlqjhrlgckf`.
- `vector` extension enabled.
- AI MVP migrations applied.
- AI tables verified.
- Backend tests pass locally in mock mode.
- Frontend typecheck and build pass locally.
- Deployment branch created: `deploy/mvp-vercel-render-supabase`.

Not completed:

- Render backend service was not created from this session.
- Vercel frontend was not redeployed from this branch.
- Final CORS URL was not set.
- End-to-end deployed dashboard-to-backend verification was not completed.

## 1. Render Backend

Use the committed `render.yaml` at the repo root.

Manual Blueprint path:

```text
https://dashboard.render.com/blueprint/new?repo=https://github.com/qurbaneliii/AI-Social-Media-Manager
```

Expected service:

- Name: `aria-llm-orchestration`
- Type: Web Service
- Runtime: Python
- Plan: Free
- Root directory: `aria/apps/llm-orchestration`
- Health check path: `/health`

Build command:

```bash
pip install --upgrade pip && pip install -e .
```

Start command:

```bash
PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set Render environment variables:

```text
DATABASE_URL=<Supabase backend-only connection string>
AI_MOCK_MODE=true
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.4
AI_MAX_RETRIES=2
AI_REQUEST_TIMEOUT_SECONDS=30
CORS_ORIGINS=<temporary localhost or later Vercel production URL>
```

Get `DATABASE_URL` from Supabase Dashboard > Connect. Use a server-side pooled or direct PostgreSQL connection string. Do not commit it and do not put it in Vercel public variables.

After deploy, verify:

```text
https://<render-service>.onrender.com/health
https://<render-service>.onrender.com/docs
https://<render-service>.onrender.com/openapi.json
https://<render-service>.onrender.com/internal/ai/workspace-context
```

## 2. Vercel Frontend

Create or update a Vercel project with:

- Root directory: `aria-frontend`
- Framework: Next.js
- Install command: `npm ci`
- Build command: `npm run build`

Set Vercel environment variables:

```text
NEXT_PUBLIC_AI_ORCHESTRATION_URL=https://<render-service>.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://<render-service>.onrender.com
NEXT_PUBLIC_API_URL=https://<render-service>.onrender.com
NEXT_PUBLIC_PREVIEW_MODE=true
NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS=45000
NEXT_PUBLIC_AI_REQUEST_RETRIES=2
```

Do not set backend secrets in Vercel frontend variables.

After deploy, verify:

```text
https://<vercel-app>.vercel.app/
https://<vercel-app>.vercel.app/login
https://<vercel-app>.vercel.app/dashboard/ai
https://<vercel-app>.vercel.app/dashboard/brand-brain
https://<vercel-app>.vercel.app/dashboard/content-studio
https://<vercel-app>.vercel.app/dashboard/strategy
https://<vercel-app>.vercel.app/dashboard/ai-analyst
https://<vercel-app>.vercel.app/dashboard/calendar-ai
https://<vercel-app>.vercel.app/dashboard/community-ai
https://<vercel-app>.vercel.app/dashboard/reports-ai
https://<vercel-app>.vercel.app/dashboard/approval
```

Use `/login` and the preview user action for demo access.

## 3. Final CORS Update

After Vercel production URL is known, update Render:

```text
CORS_ORIGINS=https://<vercel-app>.vercel.app
```

Redeploy/restart Render, then verify frontend calls to:

```text
/internal/ai/workspace-context
/internal/ai/brand-profile/validate
/internal/ai/generate-content-package
/internal/ai/brand-strategy
/internal/ai/content-calendar
/internal/ai/community/analyze
/internal/ai/approval/queue
```

Do not use wildcard CORS for the final MVP unless there is no safer free-tier path. If wildcard CORS is used temporarily, document it and remove it before sharing broadly.

## 4. OpenAI Mode Later

The first MVP deploy uses mock mode and does not require paid OpenAI API usage.

If real OpenAI mode is enabled later:

- Set `AI_MOCK_MODE=false`.
- Set a real `OPENAI_API_KEY` only on Render.
- Keep the key out of Vercel public variables.
- Document that OpenAI API billing is separate and not free.

## 5. Production Readiness Boundary

This deployment is a demo MVP only. It is not production-ready until the team adds and verifies:

- Production authentication and authorization
- Tenant isolation
- Real RLS policy design
- Observability and alerting
- Secret rotation process
- Backup and restore checks
- Rate limiting and abuse controls
- A paid/awake backend plan if cold starts are unacceptable
