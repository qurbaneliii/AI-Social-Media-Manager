# ARIA Baseline Report

Date: 2026-07-11

Branch: `codex/aria-full-architecture-ui-ux-remediation`

Base commit: `7704c8d1aa33d7032b883ff35313464a5667d5d9`

## Repository State

- Default branch checkout: `main`
- Latest local remediation branch: `codex/aria-full-architecture-ui-ux-remediation`
- Tags: none found
- Recent GitHub PR evidence:
  - PR #7 `chore: prepare free MVP deployment` was merged into `main`.
  - PR #5 `codex/vercel-supabase-production-prep` remains open and older than the merged deployment branch.
- Environment files present:
  - `.env.example`
  - `aria/.env.example`
  - `aria-frontend/.env.example`

## Runtime Baseline

- Node: `v24.15.0`
- npm: `11.12.1`
- pnpm: `11.7.0`
- Python: `3.12.10`
- Docker: `29.5.3`

## Baseline Verification

- `cd aria-frontend; npm ci`: passed, but reported 8 audit findings and deprecated vulnerable `next@15.3.2`.
- `cd aria-frontend; npm run typecheck`: passed.
- `cd aria-frontend; npm run build`: passed on D: checkout.
- `cd aria-frontend; npm run lint`: failed before remediation because `next lint` opened an interactive ESLint setup prompt.
- `PYTHONPATH=aria/apps/llm-orchestration/app AI_MOCK_MODE=true OPENAI_API_KEY=replace-me python -m pytest aria/apps/llm-orchestration/tests -q -rA`: `50 passed, 2 skipped`.

## Execution Notes

- The first C: checkout hit `ENOSPC` during `next build`; generated artifacts from that checkout were removed and the active remediation checkout moved to `D:\CodexWork\AI-Social-Media-Manager`.
- No real secret values were printed. Only example env keys were inspected.

