# Phase 6 Frontend Integration Audit

## Scope

Phase 6 connects the frontend approval dashboard to the Phase 5 backend approval queue and decision contracts. It does not add frontend publishing, scraping, platform scheduling, social media integrations, auto-replies, or direct LLM calls from the new approval UI.

## Backend Contract Summary

The LLM orchestration service exposes the approval queue and approval lifecycle routes under `/internal/ai`.

Queue routes:

- `GET /internal/ai/approval/queue`
- `GET /internal/ai/approval/queue/content`
- `GET /internal/ai/approval/queue/calendar`
- `GET /internal/ai/approval/queue/community`
- `GET /internal/ai/approval/queue/reports`

Lifecycle routes:

- `POST /internal/ai/approval/decision`
- `POST /internal/ai/approval/submit`
- `POST /internal/ai/approval/approve`
- `POST /internal/ai/approval/reject`
- `POST /internal/ai/approval/request-changes`
- `POST /internal/ai/approval/archive`
- `GET /internal/ai/approval/audit/{object_type}/{object_id}`

The queue DTOs in `aria/apps/llm-orchestration/app/ai/approval/queue.py` are the frontend source of truth. They expose normalized fields for content drafts, calendar draft items, community reply drafts, and report drafts. They intentionally hide raw JSONB storage fields such as content package, quality score, calendar item, insight payload, and metadata database blobs.

Expected backend error behavior:

- `400` for invalid filters or request shapes.
- `404` for missing approval objects.
- `409` for invalid lifecycle transitions.
- `503` when persistence is unavailable.

## Frontend Structure Summary

The active polished dashboard shell lives under `aria-frontend/app/dashboard`. It uses:

- `app/dashboard/layout.tsx`
- `components/dashboard/Sidebar.tsx`
- `components/dashboard/TopBar.tsx`
- `components/dashboard/MobileNav.tsx`
- reusable UI primitives under `components/ui`

The app also contains an older route-group dashboard under `aria-frontend/app/(dashboard)`. Phase 6 should use the existing `/dashboard/...` route family to avoid mixing shells.

## Existing Frontend AI Helper Risks

The frontend still contains direct provider-backed AI routes and helpers:

- `aria-frontend/app/api/ai/_lib.ts` imports and uses `OpenAI`.
- `aria-frontend/lib/openai.ts` constructs an OpenAI client from `OPENAI_API_KEY`.
- `aria-frontend/app/api/generate/route.ts` imports `@anthropic-ai/sdk`.
- `aria-frontend/lib/ai.ts` calls `/api/generate`.

These paths are legacy content generation helpers. They should not be used by the Phase 6 approval dashboard. New approval frontend code must call the backend internal approval routes only.

## Reusable Components

Useful existing components:

- `Button`
- `Card`
- `Badge`
- `Input`
- `Textarea`
- `Select`
- `Tabs`
- `Dialog`

Useful existing patterns:

- Dashboard pages are client components when they need state.
- The dashboard layout handles authentication through `useRequireAuth`.
- Navigation is centralized in `Sidebar`, `TopBar`, and `MobileNav`.

## Needed Frontend Additions

Pages:

- `/dashboard/approval`
- `/dashboard/approval/content`
- `/dashboard/approval/calendar`
- `/dashboard/approval/community`
- `/dashboard/approval/reports`

Optional redirect:

- `/approval` to `/dashboard/approval`

Components:

- Approval dashboard shell.
- Queue filters.
- Queue list.
- Draft detail panel.
- Audit history viewer.
- Approval action controls.

API client:

- Typed approval queue fetchers.
- Typed approval action calls.
- Typed audit history fetcher.
- Structured API error handling for `400`, `404`, `409`, and `503`.

## Testing Strategy

Backend validation:

- Run the existing LLM orchestration test suite.

Frontend validation:

- Run TypeScript checking.
- Run linting.
- Run build if dependencies and environment allow it.
- Search new approval frontend files for raw JSONB fields, direct LLM helper imports, forbidden platform integrations, and terminal states such as published, scheduled, or sent.

## Risks Before Implementation

- Phase 3.5 live database verification did not fully pass against the local Postgres credentials, so the frontend can only verify contracts and mock/unit behavior locally unless the database stack is available.
- Existing frontend AI generation helpers remain present and should be deprecated for the approval workflow without breaking existing pages.
- Backend transition rules remain authoritative. The frontend can disable common invalid actions, but backend `409` responses must still be surfaced clearly.

## Implementation Plan

1. Add a schema-first approval API client under `aria-frontend/lib/api/approval.ts`.
2. Build the approval dashboard using Phase 5 queue DTOs only.
3. Add dashboard approval pages and `/approval` redirect.
4. Add approval navigation entries to sidebar, top bar command actions, and mobile nav.
5. Add deprecation comments to legacy direct OpenAI helpers.
6. Update Phase 6 summary and architecture docs.
7. Run backend and frontend validation.
