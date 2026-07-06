# Deployment Status

Branch: `codex/vercel-supabase-production-prep`

Main deploy target: `aria-frontend` on Vercel.

Database/Auth/Storage target: Supabase.

## Current Status

- Frontend validation is configured for local runs and GitHub Actions.
- Vercel configuration is minimal and uses Next.js defaults.
- Supabase migrations are staged in `supabase/migrations/`.
- Current Prisma/JWT auth remains active; Supabase Auth migration is intentionally a later phase.
- Real secrets are not committed and must be added in Vercel/Supabase dashboards.

## Required Local Validation

Run from `aria-frontend`:

```bash
npm ci
npm run typecheck
npm run lint
npm run security:secrets
npm run build
npm run validate
npm audit --omit=dev --audit-level=high
```

## Vercel Settings

- Root directory: `aria-frontend`
- Framework preset: `Next.js`
- Install command: `npm ci`
- Build command: `npm run build`
- Output directory: `.next`
- Node.js version: `22.x` preferred, `20.x` acceptable
- Setting mode: allow Vercel to auto-detect Next.js; explicit values in `aria-frontend/vercel.json` mirror the dashboard settings.

## Supabase Staging Validation

Use a staging Supabase project before production:

```bash
npx supabase login
npx supabase link --project-ref <staging-project-ref>
npx supabase db push
```

Optional local validation when Docker is healthy:

```bash
npx supabase start
npx supabase db reset
```

## Manual Checks Before Merge

- GitHub Actions passes on the pull request.
- Vercel Preview Deployment passes.
- Supabase staging migration succeeds.
- First authenticated user can create `profiles`, `companies`, and their initial `memberships` row.
- Company members can manage company-owned resources.
- A non-member user cannot read or write another company's rows.
- `media-assets` bucket remains private and object names use `<company_id>/...`.
- Production secrets are configured in Vercel, not committed.

## Manual Checks After Merge

- Confirm Vercel production branch is `main`.
- Add production environment variables.
- Push Supabase migrations to production after staging succeeds.
- Deploy production.
- Smoke test `/login`, `/register`, `/overview`, `/posts/new`, `/scheduler`, and `/analytics`.
- Monitor Vercel function logs and Supabase Auth/API logs.
