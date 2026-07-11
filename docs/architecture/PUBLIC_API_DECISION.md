# Public API Decision

Date: 2026-07-11

## Decision

ARIA will use one browser-visible public backend entrypoint:

`NEXT_PUBLIC_API_BASE_URL`

This URL points at the deployed FastAPI application configured by `render.yaml`:

`aria/apps/llm-orchestration`

## Why

Current repository evidence shows `render.yaml` deploys only `aria/apps/llm-orchestration`, while the frontend previously called three API families:

- `/ai/*` from `aria-frontend/services/aiService.ts`
- `/v1/*` from `aria-frontend/lib/api.ts`
- `/internal/ai/*` from `aria-frontend/lib/api/ai-workspace.ts` and approval clients

The browser should not need to know whether AI orchestration is internal, in-process, or a separate service. For PR #8, the deployed FastAPI entrypoint now exposes the MVP public contracts required by the Create flow:

- `POST /v1/posts/generate`
- `GET /v1/posts/{post_id}`
- `POST /v1/posts/drafts`
- `GET /v1/companies/{company_id}/posts`
- `POST /v1/schedules`
- `GET /v1/schedules/{schedule_id}`
- `POST /v1/schedules/{schedule_id}/approve`
- canonical AI assist routes under `/internal/ai/*`

The `/v1/posts/*`, `/v1/companies/{company_id}/posts`, and `/v1/schedules/*` handlers are owned by `aria/apps/llm-orchestration/app/api/routers/public_runtime.py`. `main.py` includes this router and re-exports the current in-memory stores only for regression compatibility while persistence work remains incomplete.

## Configuration Contract

All active browser clients resolve their backend through `aria-frontend/lib/api/base.ts` and require `NEXT_PUBLIC_API_BASE_URL`. The former `NEXT_PUBLIC_AI_ORCHESTRATION_URL` and `NEXT_PUBLIC_API_URL` aliases have been removed from active runtime code and new deployment examples.

## Current Limits

- The public `/v1/posts/*` and `/v1/schedules/*` routes in `aria/apps/llm-orchestration` are MVP runtime contracts, not full production persistence replacements for the older unmounted `aria/api/*` modules.
- External platform scheduling remains not implemented. Schedule records include internal readiness only and must not be presented as confirmed external scheduling.
- Media upload and post-archive import remain owned by an unmounted legacy Core API with separate storage dependencies. Their controls are retired from the canonical Create and onboarding flows until authenticated storage ownership is implemented on the selected public backend.
- Auth and tenant enforcement are still required before PR #8 can be marked ready.
