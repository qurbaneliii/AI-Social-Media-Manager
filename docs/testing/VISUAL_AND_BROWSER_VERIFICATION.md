# Visual and Browser Verification

Date: 2026-07-11

Server under test: `npm run start -- -p 3100`

## Viewports

- Desktop: `1440 x 900`
- Mobile: `390 x 844`

## Routes Checked

| Route | Desktop | Mobile | Notes |
| --- | --- | --- | --- |
| `/posts/new` | 200 | 200 | Role-aware Create flow rendered with no console errors or failed requests. |
| `/posts` | 200 | 200 | Role-aware Content list rendered with no console errors or failed requests. |
| `/dashboard/brand` | 200 | 200 | Canonical Overview destination rendered with updated primary navigation. |
| `/dashboard/approval` | 200 | 200 | Approval page rendered and retained truthful safety copy. Backend queue request failed because the FastAPI backend was not running locally. |

## Redirect Smoke

| Source | Result |
| --- | --- |
| `/dashboard/create` | `307` to `/posts/new` |
| `/dashboard/content-studio` | `307` to `/posts/new` |
| `/dashboard/content` | `307` to `/posts` |
| `/dashboard/posts` | `307` to `/posts` |
| `/dashboard/scheduler` | `307` to `/scheduler` |
| `/dashboard/analytics` | `307` to `/analytics` |

## Retired Provider Route Smoke

| Route | Result |
| --- | --- |
| `/api/generate` | `410 FRONTEND_PROVIDER_ROUTE_RETIRED` |
| `/api/ai/generate-content` | `410 FRONTEND_PROVIDER_ROUTE_RETIRED` |
| `/api/ai/suggest-topics` | `410 FRONTEND_PROVIDER_ROUTE_RETIRED` |

## Screenshot Files

- `docs/testing/screenshots/desktop-posts-new.png`
- `docs/testing/screenshots/desktop-posts.png`
- `docs/testing/screenshots/desktop-dashboard-brand.png`
- `docs/testing/screenshots/desktop-dashboard-approval.png`
- `docs/testing/screenshots/mobile-posts-new.png`
- `docs/testing/screenshots/mobile-posts.png`
- `docs/testing/screenshots/mobile-dashboard-brand.png`
- `docs/testing/screenshots/mobile-dashboard-approval.png`

## Remaining Visual Work

The full master-prompt matrix still needs to be run after the backend is started:

- `1440 x 900`
- `1280 x 800`
- `1024 x 768`
- `768 x 1024`
- `390 x 844`
- `360 x 800`

