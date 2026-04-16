# AI-Social-Media-Manager

## Documentation

- [Full System Architecture](docs/full-system-architecture.md)

## UX Improvements (aria-frontend)

The frontend experience was redesigned to improve clarity, confidence, and speed without changing backend APIs.

- Information Architecture and Navigation:
	- Unified role-aware shell with persistent top bar, sidebar, and breadcrumbs in dashboard flows.
	- Standardized role redirects to primary routes (`/overview`, `/posts/new`, `/analytics`) to remove split-dashboard confusion.
- Content Generation Flow:
	- Replaced single long form with a 4-step guided wizard:
		1) Topic + Platforms
		2) AI Draft
		3) Review + Refine
		4) Confirm + Generate
	- Added autosave and draft recovery in local storage.
	- Added step gating and stronger inline validation before progression.
- Async Feedback and Perceived Performance:
	- Introduced reusable skeleton placeholders and applied them across loading-heavy pages.
	- Improved pending/success/error feedback for AI generation and scheduling operations.
- Empty States and Actionability:
	- Added reusable empty-state cards with clear next actions in Posts, Scheduler, Analytics, and generation subflows.
- Scheduling UX:
	- Improved manual override handling with local datetime input + UTC storage compatibility.
	- Added timeline-style schedule preview and source labels (`manual` vs `recommended`).
	- Added confirmation dialog before queueing schedules.
- Safety and Accessibility:
	- Added reusable confirmation dialog for destructive/high-impact actions.
	- Improved labeling, helper text, and submit gating in auth/onboarding forms.

These changes are focused on frontend behavior, visual clarity, and interaction quality while preserving backend contracts and API call patterns.