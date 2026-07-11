# Verification Report

Date: 2026-07-11

## Commands Run

```powershell
cd aria-frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

Results:

- `npm ci`: passed with 8 audit findings and a Next.js deprecation/security warning for `next@15.3.2`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed on the D: checkout. First retry hit a Windows `EPERM` rename while Prisma generated `query_engine-windows.dll.node`; a stale repo-owned `next start -p 3100` process was stopped and the build then passed.
- `npm run typecheck`: passed after shared navigation consolidation.
- `npm run lint`: passed after shared navigation consolidation.
- `npm run build`: passed after shared navigation consolidation.

Local production server route smoke:

```powershell
cd aria-frontend
npm run start -- -p 3100
```

| Route | Result |
| --- | --- |
| `/posts/new` | `200` |
| `/posts` | `200` |
| `/dashboard/brand` | `200` |
| `/dashboard/approval` | `200` |
| `/analytics` | `200` |
| `/scheduler` | `200` |
| `/dashboard/create` | `307` to `/posts/new` |
| `/dashboard/content-studio` | `307` to `/posts/new` |
| `POST /api/ai/generate-content` | `410`, `x-aria-deprecated-route: frontend-provider-direct` |

```powershell
$env:PYTHONPATH='aria/apps/llm-orchestration/app'
$env:AI_MOCK_MODE='true'
$env:OPENAI_API_KEY='replace-me'
python -m pytest aria/apps/llm-orchestration/tests -q -rA
```

Result after public runtime routing remediation: `58 passed, 2 skipped`.

Runtime routing contract checks:

```powershell
$env:PYTHONPATH='aria/apps/llm-orchestration/app'
$env:AI_MOCK_MODE='true'
$env:OPENAI_API_KEY='replace-me'
python -m pytest aria/apps/llm-orchestration/tests/test_public_runtime_contract.py -q
```

Result: `3 passed`.

Exact Render-entrypoint local smoke:

```powershell
cd aria/apps/llm-orchestration
$env:PYTHONPATH='app'
$env:AI_MOCK_MODE='true'
$env:OPENAI_API_KEY='replace-me'
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

| Request | Result |
| --- | --- |
| `GET /health` | `200` |
| `POST /v1/posts/generate` | `200`, returned `status=generated` and a `post_id` |
| `GET /v1/posts/{post_id}` | `200`, returned `generated_package_json` |
| `POST /ai/generate-content` | `404`, confirming legacy `/ai/*` is not deployed |

## Fixed During This Pass

- Replaced the interactive `next lint` script with an ESLint 9 flat config and `eslint .`.
- Removed frontend OpenAI/Anthropic SDK dependencies from `package.json`.
- Retired direct frontend provider API routes with explicit `410` responses.
- Rewired the legacy dashboard generator helper to call the llm-orchestration backend client.
- Fixed `/posts/new` versus `/posts` active-route matching.
- Reduced legacy shell navigation to the canonical primary IA and capped mobile navigation at five items.
- Added redirects from duplicate legacy dashboard pages to canonical role-aware pages.
- Removed fake Render `OPENAI_API_KEY=replace-me` and switched the Render branch to `main`.
- Repaired aggregate approval queue filtering and pagination semantics.
- Added regression tests for cross-type approval status filters and global aggregate pagination.
- Consolidated frontend navigation, route matching, role visibility, mobile nav, and role redirects into `aria-frontend/lib/navigation.ts`.
- Isolated legacy caption generation as explicit demo/deprecated behavior.
- Added regression tests proving the legacy adapter refuses configured provider keys instead of returning fake provider output.
- Replaced `/posts/new` AI assist calls to missing `/ai/*` routes with canonical `/internal/ai/*` backend calls.
- Added public `/v1/posts/*`, `/v1/companies/{company_id}/posts`, and `/v1/schedules/*` MVP runtime routes to the Render-deployed FastAPI entrypoint.
- Added route-contract tests for the exact Render entrypoint.

## Not Verified

- Live Vercel, Render, and Supabase deployment smoke tests were not run in this pass.
- Live database tests remain skipped without `RUN_LIVE_DB_TESTS=1` and `DATABASE_URL`.
- Full browser screenshot matrix is still required. A smoke pass was captured in `docs/testing/VISUAL_AND_BROWSER_VERIFICATION.md`.
