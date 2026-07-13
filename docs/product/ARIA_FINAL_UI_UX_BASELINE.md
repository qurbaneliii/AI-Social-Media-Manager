# ARIA Final UI/UX Baseline

Date: 2026-07-12

Starting main SHA: `3676814656bf704a7931b3a87e83ccff713c2861`

Branch: `codex/aria-final-ui-ux-redesign`

Runtime: production Next.js build on `http://127.0.0.1:3200` with the explicit preview-user path.

## Evidence Set

The baseline contains 48 viewport screenshots under `docs/product/screenshots/before/`:

- Desktop: `1440 x 900`, `1280 x 800`
- Tablet: `1024 x 768`, `768 x 1024`
- Mobile: `390 x 844`, `360 x 800`
- Routes: Overview, Brand Brain, Create, Content, Approval, Calendar, Insights, Settings

## Cross-Route Findings

| Area | Baseline evidence | Severity |
| --- | --- | --- |
| Product shell | `/dashboard/*` renders the richer dashboard shell while `/posts`, `/posts/new`, `/scheduler`, and `/analytics` render a separate role header and boxed sidebar. | Critical |
| Main landmark | Create, Content, Calendar, and Insights render two `<main>` elements because the route-group layout and pages both own the landmark. | High |
| Shared shell marker | None of the 48 captures contains `data-testid="aria-product-shell"`. | High |
| Mobile navigation | The global bottom navigation exists only in the richer dashboard layout; role-group pages expose a desktop-style sidebar on mobile. | Critical |
| Navigation source | `TopBar.tsx` duplicates navigation in a local `commandActions` array instead of using `lib/navigation.ts`. | High |
| Overview | Contains a second full content generator plus static KPI, weekly performance, and platform-distribution data. | Critical |
| Create | Uses a separate hardcoded slate/emerald visual system, a four-card stepper, and a monolithic page component. | High |
| Content | Prioritizes a raw Posts table and technical identifiers over content previews and operational state. | High |
| Calendar | Presents a schedule list rather than a planning workspace. | High |
| Insights | Uses the heading Analytics and does not consistently identify metric provenance. | High |
| Approval | Uses one oversized master-detail implementation and overflows at `768 x 1024`. | High |
| Responsive layout | Mobile Insights overflows horizontally at both required mobile widths; desktop Brand Brain, Approval, and Settings also overflow at `1440 x 900`. | High |
| Loading behavior | Overview uses an artificial minimum loading delay and several captures remain on skeleton content despite preview data being local. | Medium |
| Theme consistency | The role-group pages use hardcoded white/slate surfaces that do not follow the dashboard semantic dark-mode system. | High |

## Route Baseline

| Route | Primary issue | Mock/demo state | Accessibility/responsive issue |
| --- | --- | --- | --- |
| `/dashboard/brand` | Duplicate generator and catalogue-style metrics dominate the operational overview. | Preview banner exists, but static KPI and chart values are not labelled at component level. | Mobile capture can remain on tall skeletons; hierarchy is obscured. |
| `/dashboard/brand-brain` | Uses the richer shell but remains a large multi-panel workspace. | Default `ARIA Labs` profile is visible in preview. | Horizontal overflow at `1440 x 900`. |
| `/posts/new` | Visibly switches to the role-group shell and hardcoded visual system. | Preview behavior is available but route chrome does not carry the preview banner. | Two `<main>` landmarks; wide step controls compress on smaller screens. |
| `/posts` | Sparse developer-oriented table with raw post identity. | Preview result is present but not shaped as a content library. | Two `<main>` landmarks and no global mobile navigation. |
| `/dashboard/approval` | Dense monolithic queue/detail UI. | Empty/unconfigured persistence is represented, but action hierarchy is difficult to scan. | Horizontal overflow at tablet width. |
| `/scheduler` | Vertical schedule-ID workflow rather than calendar planning. | Internal readiness and external scheduling are not visually separated enough. | Two `<main>` landmarks and shell switch. |
| `/analytics` | Separate shell, Analytics naming, and unclear metric provenance. | Values do not consistently carry Live/Internal/Manual/Demo/Unavailable badges. | Horizontal overflow at `390 x 844` and `360 x 800`; two `<main>` landmarks. |
| `/dashboard/settings` | Uses the richer shell but exposes several product-adjacent configuration panels. | Preview account is visible. | Horizontal overflow at `1440 x 900`. |

## Baseline Acceptance Measurements

- Required screenshot count: `48/48`
- Routes with one shared ProductShell marker: `0/8`
- Canonical routes with nested `<main>`: `4/8`
- Required viewport/route combinations with horizontal overflow: `6/48`
- Duplicate content-generation entry points: `2`
- Independent navigation arrays found outside `lib/navigation.ts`: at least `1`

This is Phase 1 evidence only. The implementation continues on the same branch; these findings are not a completion claim.
