# ARIA Information Architecture

Date: 2026-07-11

## Primary Navigation

The canonical product navigation is:

1. Overview
2. Brand Brain
3. Create
4. Content
5. Calendar
6. Approval
7. Insights
8. Settings

The implementation source of truth is `aria-frontend/lib/navigation.ts`.

## Mobile Navigation

Mobile primary navigation is capped at five destinations:

1. Overview
2. Create
3. Content
4. Approval
5. More

Role visibility can reduce this list. It must not grow beyond five visible primary destinations.

## Route Decisions

| Product area | Canonical route | Duplicate or legacy routes | Status |
| --- | --- | --- | --- |
| Overview | `/dashboard/brand` | `/dashboard` | Keep canonical until the operational overview redesign lands |
| Brand Brain | `/dashboard/brand-brain` | `/dashboard/brand` overlaps partly | Needs merge of brand profile and operational overview concepts |
| Create | `/posts/new` | `/dashboard/create`, `/dashboard/content-studio` | Redirected or marked for retirement |
| Content | `/posts` | `/dashboard/content`, `/dashboard/posts` | Redirected or marked for retirement |
| Calendar | `/scheduler` | `/dashboard/scheduler`, `/dashboard/calendar-ai` | Scheduler redirected; AI calendar module needs migration |
| Approval | `/dashboard/approval` | typed approval subroutes | Keep as canonical approval inbox |
| Insights | `/analytics` | `/dashboard/analytics`, AI analyst, trends, competitors, reports AI | Needs grouping and source labels |
| Settings | `/dashboard/settings` | `/dashboard/admin` | Needs real controls only |

## Product Truthfulness Rules

- `Approved` means internally approved, not published.
- `Ready for scheduling` means internally ready, not externally scheduled.
- Analytics must show data-source labels: live integration, uploaded data, manually entered data, demo data, or mock data.
- Demo and mock mode must be visible to the user and must not silently activate in production.
