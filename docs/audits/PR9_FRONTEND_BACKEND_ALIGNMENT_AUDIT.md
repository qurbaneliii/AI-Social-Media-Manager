# PR #9 Frontend/Backend Alignment Audit

## Baseline

- Branch: `codex/aria-final-ui-ux-redesign`
- Starting SHA: `ba6c1155cb10801f59dde7946859f93d4cb2d3a4`
- Draft PR: `#9`, targeting `main`
- Canonical frontend: `aria-frontend`
- Canonical backend: `aria/apps/llm-orchestration`
- Render entrypoint: `PYTHONPATH=app uvicorn main:app --host 0.0.0.0 --port $PORT`
- Browser API base: `NEXT_PUBLIC_API_BASE_URL`
- Baseline backend tests: `57 passed, 2 skipped`; both skipped suites require live PostgreSQL.
- Baseline Ruff: failed on one unused import in `ai/approval/queue.py`.
- Local Docker/PostgreSQL: unavailable. No process `DATABASE_URL` is configured.
- Connected Supabase project: `aria-mvp-demo` is healthy. Read-only inspection found only seven `ai_*` tables. RLS is enabled but no policies exist. No workspace, membership, user, company, post, variant, or schedule tables are present in that database.

## Critical Findings

1. `api/routers/public_runtime.py` owns active `/v1/posts/*` and `/v1/schedules/*` routes but persists to module dictionaries. IDs and success responses therefore do not prove durable persistence.
2. Active public runtime routes have no authentication or tenant dependency. A caller can choose `company_id` and read or mutate records by identifier.
3. General frontend requests read only `aria_token`; real login stores `token`. Create, Content, Calendar, and Insights therefore omit the real token outside preview mode.
4. Approval sends `reviewer_id` and `reviewer_role` from the browser and the backend accepts both as authoritative.
5. Brand Brain persists to PostgreSQL when configured, but lookup is by unscoped `brand_id`; the active browser uses `/internal/ai/*` routes and client-supplied brand profiles.
6. `main.py` still owns approval and internal AI business routes directly. Public route ownership is split between `main.py` and two routers.
7. Existing AI tables lack workspace keys. Audit rows also lack trusted workspace and actor columns.
8. The redesigned Overview, Insights, and Settings pages do not consume dedicated backend contracts.
9. Calendar uses browser-local schedule IDs and the public schedule dictionary. It cannot query a persisted planning range or reliably correlate content.
10. Preview mode is visibly separated in the frontend, but production authentication and persisted non-preview E2E are not verified.

## Capability Matrix

Status values are restricted to the vocabulary required by the alignment specification.

| Product area | UI action | Frontend caller | Method | Path | Request schema | Response schema | Current route owner | Auth | Tenant enforcement | Persistence | Current status | Required action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Overview | summary counts | `useDashboardFeed` | GET | company posts + audit | path company ID | ad hoc arrays | public runtime / missing audit | none | client ID | post memory only | implemented but incompatible | Add `GET /v1/overview` database aggregation. |
| Overview | recent content | `useDashboardFeed` | GET | `/v1/companies/{id}/posts` | pagination | `PostResult[]` | public runtime | none | client ID | memory | in-memory only | Use tenant-scoped content query. |
| Overview | pending approval | Overview page | none | none | none | none | missing | none | none | none | missing | Return persisted approval counts. |
| Overview | requested changes | Overview page | none | none | none | none | missing | none | none | none | missing | Return persisted transition counts. |
| Overview | failed generation | Overview page | none | none | none | none | missing | none | none | none | missing | Return persisted generation failures. |
| Overview | Brand Brain completeness | Overview page | none | none | none | none | missing | none | none | none | missing | Include persisted completeness. |
| Overview | upcoming internal plans | Overview page | none | none | none | none | missing | none | none | none | missing | Query internal calendar range. |
| Overview | capability status | Overview page | none | none | none | none | missing | none | none | none | missing | Reuse capability service. |
| Brand Brain | load profile | `getBrandProfile` | GET | `/internal/ai/brand-profile/{id}` | brand ID | `BrandProfileResponse` | workspace router | none | unscoped ID | PostgreSQL when configured | implemented but incompatible | Move active browser contract to authenticated `/v1/brands/{id}/profile`. |
| Brand Brain | create profile | `upsertBrandProfile` | POST | `/internal/ai/brand-profile` | client profile | `BrandProfileResponse` | workspace router | none | client brand | PostgreSQL | implemented but incompatible | Resolve brand through membership and return version/timestamp. |
| Brand Brain | update profile | not used by active helper | PUT | `/internal/ai/brand-profile/{id}` | client profile | `BrandProfileResponse` | workspace router | none | unscoped ID | PostgreSQL | implemented but incompatible | Add version precondition and active frontend call. |
| Brand Brain | validate profile | `validateBrandProfile` | POST | `/internal/ai/brand-profile/validate` | profile | validation | workspace router | none | none | none required | implemented but incompatible | Authenticate and verify referenced brand. |
| Brand Brain | completeness | Brand Brain panel | POST | validation route | profile | score/missing fields | workspace router | none | none | computed only | implemented but incompatible | Add persisted completeness route. |
| Brand Brain | updated timestamp | Brand Brain panel | none | none | none | none | missing | none | none | none | missing | Return database timestamp and version. |
| Create | single generation | `generatePost` | POST | `/v1/posts/generate` | `GeneratePostForm` | post status | public runtime | none | client company | memory + orchestrator side persistence mismatch | in-memory only | Persist request, package, variants, and metadata transactionally. |
| Create | draft generation | `generateContent` | POST | `/internal/ai/generate-content-package` | client BrandProfile | package | `main.py` | bearer optional | client brand | AI draft persistence when DB exists | implemented but incompatible | Authenticate, resolve persisted Brand Brain, expose public generation router. |
| Create | multi-platform batch | `generateBatch` | repeated POST | internal generation | array in browser | per-item results | `main.py` | bearer optional | client brand | separate drafts | implemented but incompatible | Add one idempotent public batch contract. |
| Create | refine content | `improveContent` | POST | `/internal/ai/content/refine` | content/instruction | improved text | `main.py` | bearer optional | none | none | mock only | Use canonical LLM client and preserve last successful variant. |
| Create | quality review | `analyzeContent` | POST | `/internal/ai/content-quality/review` | request/package | quality review | `main.py` | bearer optional | client brand | review may persist only through orchestrator flows | implemented but incompatible | Persist review against tenant draft. |
| Create | hashtag recommendations | `suggestHashtags` | POST | `/internal/ai/hashtags/recommend` | client brand/topic | recommendation | `main.py` | bearer optional | client brand | none | implemented but incompatible | Resolve brand server-side and label mock metadata. |
| Create | topic recommendations | `suggestTopics` | POST | trends research | client company | topics | `main.py` | bearer optional | client brand | none | implemented but incompatible | Add authenticated topic recommendation contract. |
| Create | save draft | `saveDraftPost` | POST | `/v1/posts/drafts` | draft fields + company | draft status | public runtime | none | client company | memory | in-memory only | Persist draft and variant with owner from auth. |
| Create | retrieve result | `getPostResult` | GET | `/v1/posts/{id}` | post ID | `PostResult` | public runtime | none | none | memory | in-memory only | Tenant-scoped persisted detail. |
| Create | final package | `generatePost` | POST/GET | post routes | generation form | package | public runtime | none | client company | memory | in-memory only | Return persisted package and truthful mock/provider metadata. |
| Content | paginated list | `getCompanyPosts` | GET | `/v1/companies/{id}/posts` | limit/offset | items/count | public runtime | none | client company | memory | in-memory only | Add canonical `/v1/content` page contract and total. |
| Content | search | Content page | client-only | none | text | filtered current page | missing | none | none | none | missing | Database text search before pagination. |
| Content | platform filter | Content page | client-only | none | platform | filtered current page | missing | none | none | none | missing | Add query parameter. |
| Content | generation-state filter | Content page | client-only | none | status | filtered current page | missing | none | none | none | missing | Add query parameter. |
| Content | approval-state filter | Content page | none | none | status | none | missing | none | none | none | missing | Add query parameter. |
| Content | campaign/date/sort filters | Content page | none | none | filters | none | missing | none | none | none | missing | Add deterministic database filtering. |
| Content | detail retrieval | result page | GET | `/v1/posts/{id}` | post ID | package | public runtime | none | none | memory | in-memory only | Tenant-scoped persisted detail. |
| Approval | aggregate/type queue | `listApprovalQueue` | GET | `/internal/ai/approval/queue*` | filters | safe queue DTO | `main.py` | bearer optional | brand filter only | PostgreSQL | implemented but incompatible | Public authenticated router; workspace filter before pagination. |
| Approval | detail | `getApprovalDetail` | GET | `/internal/ai/approval/detail/*` | object ID/type | safe detail DTO | `main.py` | bearer optional | none | PostgreSQL | implemented but incompatible | Enforce workspace ownership. |
| Approval | audit history | `listApprovalAuditEvents` | GET | `/internal/ai/approval/audit/*` | object ID/type | events | `main.py` | bearer optional | none | PostgreSQL | implemented but incompatible | Scope and return trusted actor metadata. |
| Approval | submit/approve/reject/request changes/archive | approval client | POST | `/internal/ai/approval/*` | includes reviewer identity | `ApprovalResult` | `main.py` | bearer optional | none | two non-atomic writes | implemented but incompatible | Derive actor/role; lock row; transition and audit in one transaction. |
| Approval | calendar ready/escalate | approval client | POST | decision route | client transition | `ApprovalResult` | `main.py` | bearer optional | none | PostgreSQL | implemented but incompatible | Object-specific role and transition policy. |
| Calendar | list/date range/month/week | Scheduler page | GET per browser ID | `/v1/schedules/{id}` | schedule ID | schedule detail | public runtime | none | none | memory | in-memory only | Add `/v1/calendar/items` range/list contract. |
| Calendar | unscheduled drafts | Scheduler page | GET | company posts | company ID | posts | public runtime | none | client company | memory | implemented but incompatible | Database query excluding planned drafts. |
| Calendar | internal planned time | schedule form | POST | `/v1/schedules` | post/company/targets | IDs | public runtime | none | client company | memory | in-memory only | Persist internal calendar item, not external schedule. |
| Calendar | timezone/platform/status filters | Scheduler page | client + none | none | filters | none | missing | none | none | none | missing | Store UTC, return timezone, filter in database. |
| Calendar | planning-state update/remove | Scheduler page | POST approve only | schedule approve | optional client actor | synthetic approval | public runtime | none | none | memory | in-memory only | Add PATCH/DELETE with role checks. |
| Insights | internal content volume | Insights page | GET company posts | posts route | company ID | rows | public runtime | none | client company | memory | implemented but incompatible | Database aggregation with `source=internal`. |
| Insights | quality distribution | Insights page | client aggregation | none | rows | bars | missing | none | none | memory source | implemented but incompatible | Add `/v1/insights` aggregation. |
| Insights | approval turnaround/conversion/state | Insights page | none | none | range | none | missing | none | none | none | missing | Aggregate audit/content tables. |
| Insights | platform/planning volume | Insights page | none | none | range | none | missing | none | none | none | missing | Database aggregation with source metadata. |
| Insights | external analytics availability | Insights page | static label | none | none | unavailable | missing | none | none | none | unavailable by product design | Return explicit unavailable capability and empty series. |
| Settings | database/auth/provider/mock status | Settings page | static build checks | none | none | labels | missing | none | none | none | mock only | Add non-sensitive `/v1/capabilities`. |
| Settings | media storage | Settings page | none | none | none | unavailable | missing | none | none | none | unavailable by product design | Return unavailable reason code. |
| Settings | external scheduling/publishing/analytics | Settings page | none | none | none | unavailable | missing | none | none | none | unavailable by product design | Return explicit unavailable states. |
| Settings | background workers | Settings page | none | none | none | unavailable | missing | none | none | none | unavailable by product design | Return unavailable status until health is verifiable. |

## Required Migration Direction

The live Supabase schema proves that tenant identity cannot be added only in application code. A forward migration is required to introduce workspace membership and tenant keys, variant persistence, trusted audit actors, and internal calendar relationships. Applying that migration to the connected primary project is intentionally deferred until it is verified on an isolated development database or explicitly authorized for the primary database.

