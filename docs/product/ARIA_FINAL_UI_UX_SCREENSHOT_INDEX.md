# ARIA Before/After Screenshot Index

The complete evidence set contains 48 baseline screenshots and 96 final screenshots captured from the production-built server in explicit preview mode. Final screenshots cover all eight routes at six required viewport sizes in both light and dark themes. Machine-readable results are in [`verification.json`](screenshots/after/verification.json); all 96 checks passed with zero console errors, page errors, failed requests, shell-marker failures, main-landmark failures, or horizontal overflow.

## Route Index

| Route | URL | Before desktop | After light desktop | After dark mobile |
| --- | --- | --- | --- | --- |
| Overview | `/dashboard/brand` | [1440x900](screenshots/before/desktop/overview-1440x900.png) | [1440x900](screenshots/after/light/desktop/overview-1440x900.png) | [390x844](screenshots/after/dark/mobile/overview-390x844.png) |
| Brand Brain | `/dashboard/brand-brain` | [1440x900](screenshots/before/desktop/brand-brain-1440x900.png) | [1440x900](screenshots/after/light/desktop/brand-brain-1440x900.png) | [390x844](screenshots/after/dark/mobile/brand-brain-390x844.png) |
| Create | `/posts/new` | [1440x900](screenshots/before/desktop/create-1440x900.png) | [1440x900](screenshots/after/light/desktop/create-1440x900.png) | [390x844](screenshots/after/dark/mobile/create-390x844.png) |
| Content | `/posts` | [1440x900](screenshots/before/desktop/content-1440x900.png) | [1440x900](screenshots/after/light/desktop/content-1440x900.png) | [390x844](screenshots/after/dark/mobile/content-390x844.png) |
| Approval | `/dashboard/approval` | [1440x900](screenshots/before/desktop/approval-1440x900.png) | [1440x900](screenshots/after/light/desktop/approval-1440x900.png) | [390x844](screenshots/after/dark/mobile/approval-390x844.png) |
| Calendar | `/scheduler` | [1440x900](screenshots/before/desktop/calendar-1440x900.png) | [1440x900](screenshots/after/light/desktop/calendar-1440x900.png) | [390x844](screenshots/after/dark/mobile/calendar-390x844.png) |
| Insights | `/analytics` | [1440x900](screenshots/before/desktop/insights-1440x900.png) | [1440x900](screenshots/after/light/desktop/insights-1440x900.png) | [390x844](screenshots/after/dark/mobile/insights-390x844.png) |
| Settings | `/dashboard/settings` | [1440x900](screenshots/before/desktop/settings-1440x900.png) | [1440x900](screenshots/after/light/desktop/settings-1440x900.png) | [390x844](screenshots/after/dark/mobile/settings-390x844.png) |

## Directory Layout

- Baseline: `docs/product/screenshots/before/{desktop,tablet,mobile}`
- Final light: `docs/product/screenshots/after/light/{desktop,tablet,mobile}`
- Final dark: `docs/product/screenshots/after/dark/{desktop,tablet,mobile}`
