# ARIA Architecture Decisions

Date: 2026-07-11

## ADR-001: Canonical Frontend Runtime

Decision: `aria-frontend` is the canonical frontend application.

Evidence:

- Vercel deployment work targets `aria-frontend`.
- The build, lint, and typecheck validation all run from `aria-frontend`.
- The role-aware `/posts/new`, `/posts`, `/scheduler`, and `/analytics` flows live there.

Consequence:

- Nested dashboard experiments and root-level dashboard apps must not become parallel product surfaces.

## ADR-002: Canonical AI Backend

Decision: `aria/apps/llm-orchestration` is the canonical AI orchestration backend.

Evidence:

- `render.yaml` points at the llm-orchestration service.
- The tested backend suite lives under `aria/apps/llm-orchestration/tests`.
- The current AI workspace and approval clients call `/internal/ai/*` on this service.

Consequence:

- Frontend provider routes are compatibility tombstones only.
- Legacy `/run` and `LiteLLMAdapter` behavior are not canonical provider paths.
- Legacy caption generation is explicitly demo-only and must not handle configured provider keys.

## ADR-003: Canonical Navigation Source

Decision: `aria-frontend/lib/navigation.ts` owns navigation labels, route matching, role visibility, mobile primary destinations, and default role redirects.

Evidence:

- The role-aware shell, legacy dashboard sidebar, mobile navigation, and login redirect previously duplicated route arrays.
- Duplicate route matching caused `/posts/new` and `/posts` active-state risk.

Consequence:

- New visible navigation items must be added to `lib/navigation.ts`.
- Mobile secondary destinations must be exposed through the `More` drawer, not added as extra bottom-navigation items.
- Route-specific role checks in UI components should be treated as display hints only, not security.

## ADR-004: Truthful MVP Deployment

Decision: The production-like MVP path is Vercel frontend, Render backend, and Supabase database/auth-aligned storage.

Consequence:

- GitHub Pages/static export may exist only as an explicit demo path.
- Production must not silently fall back to localhost, mock data, or fake provider results.

## ADR-005: Legacy Provider Isolation

Decision: `LiteLLMAdapter` in `main.py` is isolated as a legacy demo adapter. It refuses configured provider keys and no longer reports fabricated token usage.

Evidence:

- The canonical provider path is `ai/llm/client.py` through `AIOrchestrator`.
- The legacy caption endpoint creates deterministic variants locally and is not a real provider call.

Consequence:

- `/internal/captions/generate` emits `x-aria-deprecated-route: legacy-caption-generator` and `x-aria-demo-mode: true`.
- `/run` emits `x-aria-deprecated-route: legacy-orchestration-run`.
- Any future real caption generation must use the canonical backend AI gateway rather than re-enabling this adapter.

## ADR-006: Backend Router Extraction

Decision: `main.py` should initialize the FastAPI app and include routers; route families should move out in reviewable slices.

Evidence:

- The public `/v1/posts/*`, `/v1/companies/{company_id}/posts`, and `/v1/schedules/*` contracts are now isolated in `api/routers/public_runtime.py`.
- Runtime dependencies shared by route modules live in `api/dependencies.py`.
- Existing public runtime tests still import the app through `main.py`, proving the deployed Render entrypoint remains stable.

Consequence:

- Future backend route extraction should preserve public contracts and add or keep route registration tests before moving behavior.
- Internal AI, approval, Brand Brain, and legacy route families still need later router splits.
