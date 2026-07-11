# PR #8 Runtime Contract Audit

Date: 2026-07-11

Branch: `codex/aria-full-architecture-ui-ux-remediation`

## Critical Finding

Before this pass, the canonical `/posts/new` flow could call three backend contract families:

- `aria-frontend/services/aiService.ts` -> `/ai/*`
- `aria-frontend/lib/api.ts` -> `/v1/*`
- `aria-frontend/lib/api/ai-workspace.ts` and approval client -> `/internal/ai/*`

`render.yaml` deploys `aria/apps/llm-orchestration`, which exposed `/internal/ai/*` but not the legacy `/ai/*` routes or the public `/v1/posts/*` routes used by the frontend.

## Public API Decision

The browser-visible API base is `NEXT_PUBLIC_API_BASE_URL`.

Compatibility fallbacks remain for existing environments:

- `NEXT_PUBLIC_AI_ORCHESTRATION_URL`
- `NEXT_PUBLIC_API_URL`

New deployments should not set separate public AI and core API URLs.

## Runtime Route Mapping

| Frontend operation | Source function | Previous URL | Current URL | Backend handler |
| --- | --- | --- | --- | --- |
| Generate AI draft | `generateContent` in `services/aiService.ts` | `/ai/generate-content` | `/internal/ai/generate-content-package` | `ai_generate_content_package` |
| Batch generation | `generateBatch` in `services/aiService.ts` | `/ai/generate-batch` | frontend fan-out to `/internal/ai/generate-content-package` | `ai_generate_content_package` |
| Improve content | `improveContent` in `services/aiService.ts` | `/ai/improve-content` | `/internal/ai/content/refine` | `ai_refine_content` |
| Analyze content | `analyzeContent` in `services/aiService.ts` | `/ai/analyze-content` | `/internal/ai/content-quality/review` | `ai_review_content_quality` |
| Suggest hashtags | `suggestHashtags` in `services/aiService.ts` | `/ai/suggest-hashtags` | `/internal/ai/hashtags/recommend` | `ai_recommend_hashtags` |
| Suggest topics | `suggestTopics` in `services/aiService.ts` | `/ai/suggest-topics` | `/internal/ai/trends/research` | `ai_research_trends` |
| Final post generation | `generatePost` in `lib/api.ts` | `/v1/posts/generate` | `/v1/posts/generate` | `public_generate_post` |
| Retrieve generated post | `getPostResult` in `lib/api.ts` | `/v1/posts/{post_id}` | `/v1/posts/{post_id}` | `public_get_post` |
| Save draft | `saveDraftPost` in `lib/api.ts` | `/v1/posts/drafts` | `/v1/posts/drafts` | `public_save_draft` |
| List company posts | `getCompanyPosts` in `lib/api.ts` | `/v1/companies/{company_id}/posts` | `/v1/companies/{company_id}/posts` | `public_list_company_posts` |
| Create schedule | `createSchedule` in `lib/api.ts` | `/v1/schedules` | `/v1/schedules` | `public_create_schedule` |
| Retrieve schedule | `getSchedule` in `lib/api.ts` | `/v1/schedules/{schedule_id}` | `/v1/schedules/{schedule_id}` | `public_get_schedule` |
| Approve schedule | `approveSchedule` in `lib/api.ts` | `/v1/schedules/{schedule_id}/approve` | `/v1/schedules/{schedule_id}/approve` | `public_approve_schedule` |

## Verified Contract Tests

`aria/apps/llm-orchestration/tests/test_public_runtime_contract.py` verifies:

- the exact Render FastAPI entrypoint exposes every frontend-required Create-flow route listed above;
- a non-preview public post generation, retrieval, draft save, list, schedule create, schedule detail, and schedule approval flow works through the deployed app object;
- legacy `/ai/*` routes are not part of the deployed backend contract.

## Current Response Schemas

- AI assist responses are adapted from canonical typed AI workspace responses into the existing Create page view model.
- `/v1/posts/generate` returns `post_id`, `status`, and `estimated_ready_seconds`.
- `/v1/posts/{post_id}` returns `post_id`, `status`, and `generated_package_json`.
- `/v1/posts/drafts` returns `post_id`, `status`, `platform`, and `created_at`.
- `/v1/schedules` returns `schedule_ids` and `status`.
- `/v1/schedules/{schedule_id}` includes `external_scheduling_status: not_implemented` so the UI must not claim external platform scheduling.

## Not Yet Complete

- Public `/v1` routes in `aria/apps/llm-orchestration/app/api/routers/public_runtime.py` currently provide the MVP runtime contract and route ownership for PR #8; full production persistence and auth still need Phase J/K work.
- Actor identity is still not derived from trusted backend authentication context.
- Live PostgreSQL integration for these new public routes has not been completed in this pass.
- Browser Playwright non-preview happy-path testing remains required.
