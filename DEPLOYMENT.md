# Production Deployment Guide

This repository is a mixed AI social media manager monorepo. The production-friendly path is to deploy the interactive web app from `aria-frontend` to Vercel and use Supabase for PostgreSQL, Auth, Storage, and persisted application data.

## Detected Structure

- `aria-frontend/`: Next.js 15 App Router frontend with API routes for auth and AI provider calls.
- `aria-frontend/prisma/`: Current Prisma schema for the existing custom email/password auth routes.
- `aria/db/migrations/`: Existing service-oriented PostgreSQL migrations that use custom session-setting RLS.
- `apps/` and `aria/apps/`: Python/FastAPI and service modules for content analysis, scheduling, LLM orchestration, and related backend capabilities.
- `docker-compose.yml`: Local service stack with Postgres, Redis, Kafka, Temporal, and multiple API containers.
- `supabase/`: Production Supabase migration/config entrypoint added for cloud/local Supabase.

## Target Architecture

- Vercel hosts `aria-frontend` as a dynamic Next.js app.
- Next.js API routes handle lightweight AI calls and current auth routes.
- Supabase provides PostgreSQL, Auth, private media storage, and durable data tables.
- AI provider keys stay server-side only in Vercel environment variables.
- The existing long-running Docker services, Kafka, and Temporal workers are not a good fit for Vercel Serverless. Keep them on a container platform if they are required for production automation.

## Required Accounts

- GitHub account with access to this repository.
- Vercel account connected to GitHub.
- Supabase account and project.
- AI provider account keys for OpenAI and/or Anthropic.
- Social platform developer credentials if publishing integrations are enabled.

## Supabase Setup

1. Create a Supabase project.
2. In SQL Editor, enable the `vector` extension if prompted by the migration.
3. Apply migrations from this repo:

```bash
supabase link --project-ref <your-project-ref>
supabase db push
```

If you do not use the Supabase CLI, paste and run the files in order from `supabase/migrations/` in the Supabase SQL Editor.

4. Optionally load seed data:

```bash
supabase db reset
```

or paste `supabase/seed.sql` into SQL Editor after migrations.

5. Confirm the `media-assets` storage bucket exists and is private.
6. Store uploaded objects under a company-prefixed path, for example `<company_id>/uploads/logo.png`, so storage RLS can verify membership.

## Supabase Auth URLs

In Supabase Dashboard, configure Auth URL settings:

- Site URL, local: `http://localhost:3000`
- Site URL, production: `https://<your-vercel-domain>`
- Redirect URLs:
  - `http://localhost:3000/oauth/callback`
  - `https://<your-vercel-domain>/oauth/callback`

The frontend currently still has custom Prisma/JWT auth routes. The Supabase schema is ready for Supabase Auth, but fully switching UI auth flows to Supabase Auth should be a separate, tested migration.

## Vercel Settings

Import the GitHub repository into Vercel and use these settings:

- Root directory: `aria-frontend`
- Framework preset: `Next.js`
- Install command: `npm ci`
- Build command: `npm run build`
- Output directory: `.next`
- Node.js version: `20.x` or `22.x`

The file `aria-frontend/vercel.json` mirrors these settings for the frontend project.

## Vercel Environment Variables

Add these in Vercel Project Settings. Variables with `NEXT_PUBLIC_` are browser-visible and must never contain secrets.

| Variable | Required | Runtime | Exposure | Vercel scope | Example |
| --- | --- | --- | --- | --- | --- |
| `NEXT_PUBLIC_APP_URL` | Yes | Frontend | Public | Production, Preview, Development | `https://<your-vercel-domain>` |
| `NEXT_PUBLIC_API_BASE_URL` | Required when external backend APIs are used | Frontend | Public | Production, Preview, Development | `https://<backend-api-domain>` |
| `NEXT_PUBLIC_API_URL` | Optional legacy alias for older modules | Frontend | Public | Production, Preview, Development | `https://<backend-api-domain>` |
| `NEXT_PUBLIC_AI_ORCHESTRATION_URL` | Optional | Frontend | Public | Production, Preview, Development | `https://<llm-orchestration-domain>` |
| `NEXT_PUBLIC_SUPABASE_URL` | Required for Supabase REST/Auth/Storage clients | Frontend/server | Public | Production, Preview, Development | `https://<project-ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Required for browser Supabase access | Frontend | Public | Production, Preview, Development | `<supabase-anon-key>` |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional until server routes use Supabase admin operations | Server route only | Secret | Production only unless using a separate staging project for Preview | `<supabase-service-role-key>` |
| `DATABASE_URL` | Required while custom Prisma/JWT auth is active | Server route/build | Secret | Production; Preview only with a separate staging database | `<supabase-postgres-connection-string>` |
| `JWT_SECRET` | Required while custom Prisma/JWT auth is active | Server route | Secret | Production, Preview, Development | `<long-random-secret>` |
| `OPENAI_API_KEY` | Required for `app/api/ai/*` routes | Server route | Secret | Production; Preview only with a non-production key | `<openai-api-key>` |
| `OPENAI_MODEL` | Optional | Server route | Server-only value | Production, Preview, Development | `gpt-4o-mini` |
| `OPENAI_REQUEST_TIMEOUT_MS` | Optional | Server route | Server-only value | Production, Preview, Development | `45000` |
| `OPENAI_MAX_RETRIES` | Optional | Server route | Server-only value | Production, Preview, Development | `2` |
| `ANTHROPIC_API_KEY` | Required only for `/api/generate` | Server route | Secret | Production; Preview only with a non-production key | `<anthropic-api-key>` |
| `NEXT_PUBLIC_PREVIEW_MODE` | Optional | Frontend | Public | Preview, Development; set `false` or omit in Production | `false` |
| `NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS` | Optional | Frontend | Public | Production, Preview, Development | `45000` |
| `NEXT_PUBLIC_AI_REQUEST_RETRIES` | Optional | Frontend | Public | Production, Preview, Development | `2` |

Set `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_API_URL` to the same backend URL until the older `NEXT_PUBLIC_API_URL` usage is removed. For a frontend-only preview with mock data, set `NEXT_PUBLIC_PREVIEW_MODE=true` and leave external backend URLs pointed at safe non-production endpoints.

Never add `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DATABASE_URL`, or `JWT_SECRET` with a `NEXT_PUBLIC_` prefix.

## Validation Commands

From `aria-frontend`:

```bash
npm ci
npm run typecheck
npm run lint
npm run security:secrets
npm run build
npm run validate
npm audit --omit=dev --audit-level=high
```

`npm run security:secrets` blocks accidental browser references to server-only variables and browser imports of `lib/supabase/server`.

## Local Frontend Validation

From `aria-frontend`:

```bash
npm ci
npm run typecheck
npm run lint
npm run build
npm run dev
```

Use `.env.local` for real local secrets. Do not commit `.env.local`.

## Production Smoke Test

After Vercel deploys:

1. Open the production URL.
2. Confirm `/login`, `/register`, `/overview`, `/posts/new`, `/scheduler`, and `/analytics` render.
3. Exercise an AI generation route only after server-side AI keys are configured.
4. Verify Supabase can read authenticated rows only for the signed-in user's company membership.
5. Test first-user bootstrap: create an Auth user, insert `profiles.id = auth.uid()`, create a `companies.created_by = auth.uid()` row, then insert that user's first `memberships` row for the new company.
6. Upload a media object to `media-assets` using a `<company_id>/...` path and confirm another user without membership cannot read it.

## Merge Checklist

Before merging this branch:

- GitHub Actions `Validate Vercel Frontend` passes.
- Vercel Preview Deployment for the branch passes with the `aria-frontend` root directory.
- Supabase staging migrations apply with `supabase db push`.
- First-user company bootstrap is tested in staging.
- A second authenticated user without membership cannot read or write the first company data.
- The private `media-assets` bucket rejects another company's object paths and unauthenticated reads.
- Vercel Production/Preview/Development environment variables are configured with no real secrets committed.

After merging:

- Connect or confirm the Vercel project production branch is `main`.
- Configure production Vercel environment variables.
- Run Supabase production migrations deliberately after staging succeeds.
- Deploy production, smoke test key routes, and monitor Vercel/Supabase logs.

## Common Deployment Errors

- `NEXT_NOT_FOUND` or wrong app detected: Vercel root directory is not set to `aria-frontend`.
- `PrismaClientInitializationError`: `DATABASE_URL` is missing or points to a database without the Prisma auth migration.
- `OPENAI_API_KEY is not configured`: the AI API routes are deployed but the server-side key is missing.
- Browser requests cannot reach backend APIs: `NEXT_PUBLIC_API_BASE_URL` still points to `localhost` in Vercel.
- Supabase REST returns permission errors: run the migrations, confirm RLS policies, and confirm grants exist for `authenticated`.
- Media upload succeeds but metadata read fails: make sure the object path and `media_assets.storage_path` match exactly.

## Security Notes

- RLS is enabled for all public app tables created by the Supabase migration.
- The service role key is only for server-side code and must never be exposed to browser bundles.
- Social account tokens are modeled as encrypted fields; encryption/decryption must happen server-side.
- Long-running schedulers, Temporal workers, Kafka consumers, and Docker-only services should not be moved into Vercel functions without redesigning them for serverless constraints.
