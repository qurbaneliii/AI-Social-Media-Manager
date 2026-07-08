# Vercel Frontend Deployment Status

Status: Preview deployment exists, but target frontend is not correctly deployed.
Date: 2026-07-08

## Vercel Project URL

No verified Vercel production deployment URL was produced from this branch.

GitHub/Vercel integration created preview deployments from this branch, but none are the requested frontend deployment.

Latest checked deployment from commit `b287f8efae03ef8c841524871810b1f0b96f38ed`:

- Project: `ai-social-media-manager-gl7x`
- Deployment id: `dpl_3boLrFXUQs41un26ojfQ8nTXioyH`
- Alias: `https://ai-social-media-manager-gl7x-git-d-7b3aa9-qurbaneliiis-projects.vercel.app`
- State: `READY`
- Result: not usable as the MVP frontend because build logs show `Skipping cache upload because no files were prepared`.

Earlier checked deployment from commit `3147f0cfa2e5976c175f9edbbc32fda273d5ba68`:

- Project: `ai-social-media-manager-gl7x`
- Deployment id: `dpl_4jVE8ni9jMNWueGRu5kN3CEZprib`
- Alias: `https://ai-social-media-manager-gl7x-git-d-7b3aa9-qurbaneliiis-projects.vercel.app`
- State: `READY`
- Result: not usable as the MVP frontend because the build log shows the repo root was built and no files were prepared; `/dashboard/ai` returned Vercel `404`.

Existing Vercel context found through the connected Vercel tool:

- Project `ai-social-media-manager`
  - Project id: `prj_jMasGlzupK0ArFjO3teilV7EZA2r`
  - Latest branch deployment state: `ERROR`
  - Latest error: configured root directory `mainn` does not exist
  - Domain context: `ai-social-media-manager-phi.vercel.app`
- Project `ai-social-media-manager-gl7x`
  - Project id: `prj_PHVqgNyhoeVW3pPVHMT5nVL6AJiC`
  - Latest production deployment state: `READY`
  - Domain context: `ai-social-media-manager-gl7x.vercel.app`
  - Verification result: root and `/dashboard/ai` returned Vercel `404`, so it is not a verified ARIA MVP deployment.

## Root Directory

Target Vercel root directory:

```text
aria-frontend
```

## Build Settings

Added `aria-frontend/vercel.json`:

```json
{
  "framework": "nextjs",
  "installCommand": "npm ci",
  "buildCommand": "npm run build"
}
```

Package manager:

- npm, based on `aria-frontend/package-lock.json`

## Environment Variables Required

Safe frontend variables:

- `NEXT_PUBLIC_AI_ORCHESTRATION_URL=<Render backend URL>`
- `NEXT_PUBLIC_API_BASE_URL=<Render backend URL>` if needed by older clients
- `NEXT_PUBLIC_API_URL=<Render backend URL>` if needed by older clients
- `NEXT_PUBLIC_PREVIEW_MODE=true`
- `NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS=45000`
- `NEXT_PUBLIC_AI_REQUEST_RETRIES=2`

Do not set these in Vercel frontend public variables:

- Supabase database URL
- Supabase service role key
- OpenAI API key
- Render backend secrets

## Build Result

Local frontend checks completed:

```bash
cd aria-frontend
npm install
npm run typecheck
npm run build
```

Result:

- TypeScript check passed.
- Next.js build passed.
- Build generated the target dashboard pages.

Important fix:

- Added `prebuild: prisma generate` so Next.js can import `@prisma/client` during route collection.

## Frontend Pages Verified

Local build output included:

- `/dashboard/ai`
- `/dashboard/brand-brain`
- `/dashboard/content-studio`
- `/dashboard/strategy`
- `/dashboard/ai-analyst`
- `/dashboard/calendar-ai`
- `/dashboard/community-ai`
- `/dashboard/reports-ai`
- `/dashboard/approval`

Live deployed browser verification was not completed because no new Vercel deployment was created and the Render backend URL is not available.

## Auth Behavior

Dashboard pages use client-side auth state. The login page exposes a preview path:

- Go to `/login`
- Use the "Continue as Preview User" action
- Preview credentials in UI: `preview@ariaconsole.com` / `Preview123!`

This is demo access only. It is not production authentication.

## Known Vercel Free-Tier Limitations

- Free-tier build/runtime limits apply.
- Serverless execution limits apply to any Next.js API routes.
- This MVP should call the Render FastAPI service for AI orchestration through `NEXT_PUBLIC_AI_ORCHESTRATION_URL`.

## Blocker

The session did not have non-interactive Vercel deployment/env write access:

- No Vercel project-root/settings write tool was exposed.
- No Vercel environment-variable write tool was exposed.
- The Render backend URL is not available yet, so the required frontend API URL cannot be set.
- `BLOCKED_VERCEL_TOOL_ACCESS: Vercel project/root-directory/env-var write operations are not available through connected tools. User must manually create/update Vercel project.`
