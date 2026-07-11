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
- Legacy `/run` and `LiteLLMAdapter` behavior must be isolated or retired in a later phase.

## ADR-003: Canonical Navigation Source

Decision: `aria-frontend/lib/navigation.ts` owns navigation labels, route matching, role visibility, mobile primary destinations, and default role redirects.

Evidence:

- The role-aware shell, legacy dashboard sidebar, mobile navigation, and login redirect previously duplicated route arrays.
- Duplicate route matching caused `/posts/new` and `/posts` active-state risk.

Consequence:

- New visible navigation items must be added to `lib/navigation.ts`.
- Route-specific role checks in UI components should be treated as display hints only, not security.

## ADR-004: Truthful MVP Deployment

Decision: The production-like MVP path is Vercel frontend, Render backend, and Supabase database/auth-aligned storage.

Consequence:

- GitHub Pages/static export may exist only as an explicit demo path.
- Production must not silently fall back to localhost, mock data, or fake provider results.
