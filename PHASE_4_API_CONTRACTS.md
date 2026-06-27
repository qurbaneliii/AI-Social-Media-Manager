# Phase 4 API Contracts

Phase 4 adds backend-only approval lifecycle contracts for AI-generated drafts. These routes do not publish content, schedule content to real platforms, send community replies, scrape data, or call social platform APIs.

## Approval States

Content drafts:

- `draft`
- `in_review`
- `approved`
- `rejected`
- `changes_requested`
- `archived`

Quality reviews:

- `generated`
- `reviewed`
- `superseded`

Calendar draft items:

- `draft`
- `in_review`
- `approved`
- `rejected`
- `changes_requested`
- `ready_for_scheduling`
- `archived`

Community reply drafts:

- `draft`
- `in_review`
- `approved`
- `rejected`
- `changes_requested`
- `escalated`
- `archived`

`approved` does not mean published. `ready_for_scheduling` does not mean scheduled to a platform. Approved community replies are never sent automatically in Phase 4.

## Approval Decision Schema

```json
{
  "object_id": "content-draft-uuid",
  "object_type": "content_draft",
  "previous_status": "draft",
  "new_status": "approved",
  "action": "approve",
  "reviewer_id": "user-123",
  "reviewer_role": "brand_manager",
  "reason": "Matches brand voice.",
  "requested_changes": [],
  "timestamp": "2026-06-19T00:00:00Z",
  "metadata": {}
}
```

`object_type` values:

- `content_draft`
- `calendar_draft`
- `community_reply`
- `report_draft`

## Action Request Schema

Action-specific routes accept:

```json
{
  "object_id": "content-draft-uuid",
  "object_type": "content_draft",
  "reviewer_id": "user-123",
  "reviewer_role": "brand_manager",
  "reason": "Approved for later use.",
  "requested_changes": [],
  "metadata": {}
}
```

The route sets the lifecycle `action` and `new_status`.

## Response Schema

Approval routes return:

```json
{
  "decision": {
    "object_id": "content-draft-uuid",
    "object_type": "content_draft",
    "previous_status": "draft",
    "new_status": "approved",
    "action": "approve",
    "reviewer_id": "user-123",
    "reviewer_role": "brand_manager",
    "reason": "Approved for later use.",
    "requested_changes": [],
    "timestamp": "2026-06-19T00:00:00Z",
    "metadata": {}
  },
  "audit_event": {
    "event_id": "approval-event-uuid",
    "object_id": "content-draft-uuid",
    "object_type": "content_draft",
    "previous_status": "draft",
    "new_status": "approved",
    "action": "approve",
    "reviewer_id": "user-123",
    "reviewer_role": "brand_manager",
    "reason": "Approved for later use.",
    "requested_changes": [],
    "timestamp": "2026-06-19T00:00:00Z",
    "metadata": {}
  },
  "record": {}
}
```

## Routes

- `POST /internal/ai/approval/decision`: generic approval decision route.
- `POST /internal/ai/approval/submit`: sets status to `in_review`.
- `POST /internal/ai/approval/approve`: sets status to `approved`.
- `POST /internal/ai/approval/reject`: sets status to `rejected`.
- `POST /internal/ai/approval/request-changes`: sets status to `changes_requested`.
- `POST /internal/ai/approval/archive`: sets status to `archived`.
- `GET /internal/ai/approval/audit/{object_type}/{object_id}`: lists approval audit events.
- `GET /internal/ai/approval/queue`: lists all approval queue item types using frontend-safe DTOs.
- `GET /internal/ai/approval/queue/content`: lists content draft queue items.
- `GET /internal/ai/approval/queue/calendar`: lists calendar draft queue items.
- `GET /internal/ai/approval/queue/community`: lists community reply queue items.
- `GET /internal/ai/approval/queue/reports`: lists report draft queue items.
- `GET /internal/ai/drafts/content`: legacy alias for content draft queue items.
- `GET /internal/ai/drafts/calendar`: legacy alias for calendar draft queue items.
- `GET /internal/ai/drafts/community`: legacy alias for community reply queue items.

Queue routes support optional filters:

- `brand_id`
- `status`
- `object_type`
- `platform`
- `limit`
- `offset`
- `created_after`
- `created_before`

Draft/queue list routes return:

```json
{
  "items": [],
  "count": 0,
  "limit": 50,
  "offset": 0
}
```

Queue item responses do not expose raw database JSON blobs such as `content_package_json`, `quality_scores_json`, `calendar_item_json`, `insight_payload_json`, or `metadata_json`. They expose preview fields and summarized status/score metadata for approval queue clients.

Example content queue item:

```json
{
  "object_id": "content-draft-uuid",
  "object_type": "content_draft",
  "draft_id": "content-draft-uuid",
  "brand_id": "brand-1",
  "platform": "linkedin",
  "content_type": "post",
  "topic": "approval workflow",
  "hook_preview": "A short hook preview",
  "caption_preview": "A short caption preview",
  "approval_status": "draft",
  "requires_human_review": true,
  "risk_summary": [],
  "quality_score_summary": {
    "brand_consistency_score": 0.9,
    "approval_status": "requires_human_review"
  },
  "created_at": "2026-06-19T00:00:00Z",
  "updated_at": "2026-06-19T00:00:00Z",
  "model": "gpt-4o-mini",
  "mock_mode": true
}
```

## Phase 7 Detail Routes

Phase 7 adds safe detail contracts for human review. These routes return curated DTOs and latest audit timeline entries; they do not return raw database JSONB blobs.

- `GET /internal/ai/approval/detail/content/{draft_id}`
- `GET /internal/ai/approval/detail/calendar/{item_id}`
- `GET /internal/ai/approval/detail/community/{reply_draft_id}`
- `GET /internal/ai/approval/detail/reports/{report_id}`
- `GET /internal/ai/approval/detail/{object_type}/{object_id}`

Content detail response fields:

- `draft_id`
- `object_type`
- `brand_id`
- `platform`
- `content_type`
- `topic`
- `hook`
- `caption`
- `cta`
- `hashtags`
- `visual_brief_summary`
- `video_script_summary`
- `carousel_structure_summary`
- `posting_recommendation`
- `rationale`
- `risk_summary`
- `quality_score_summary`
- `approval_status`
- `requires_human_review`
- `model`
- `mock_mode`
- `prompt_version`
- `created_at`
- `updated_at`
- `latest_audit_events`
- `last_requested_changes`
- `last_review_reason`

Calendar, community, and report detail responses follow the same pattern: a stable id, `object_type`, `brand_id`, curated review fields, status, timestamps, latest audit events, and latest request-changes context.

Detail route errors:

- Missing record: `404 Not Found`.
- Invalid generic `object_type`: `400 Bad Request`.
- Persistence unavailable: `503 Service Unavailable`.

Request changes remains an approval lifecycle action. The request must include a `reason` and may include `requested_changes`; the frontend requires both a reason and at least one requested change before submitting. The backend records these values in the audit event and returns them through audit/detail DTOs. It does not regenerate or overwrite the draft.

## Transition Behavior

Invalid transitions return `409 Conflict` with:

```json
{
  "detail": "Invalid content_draft transition: approved -> draft",
  "object_type": "content_draft",
  "previous_status": "approved",
  "new_status": "draft"
}
```

Missing records return `404 Not Found` with:

```json
{
  "detail": "content_draft not found: missing-id",
  "object_type": "content_draft",
  "object_id": "missing-id"
}
```

If `DATABASE_URL` is not configured and persistence routes are called, the service returns `503`.

Invalid queue filters return `400 Bad Request`, for example when requesting `status=escalated` for a calendar queue.

## Examples

Approve:

```json
{
  "object_id": "content-draft-uuid",
  "object_type": "content_draft",
  "reviewer_id": "reviewer-1",
  "reviewer_role": "brand_manager",
  "reason": "Approved for internal draft queue."
}
```

Reject:

```json
{
  "object_id": "content-draft-uuid",
  "object_type": "content_draft",
  "reviewer_id": "reviewer-1",
  "reason": "Does not match the campaign brief."
}
```

Request changes:

```json
{
  "object_id": "calendar-item-uuid",
  "object_type": "calendar_draft",
  "reviewer_id": "reviewer-1",
  "reason": "Needs timing adjustment.",
  "requested_changes": ["Move this post to the following week."]
}
```

## Safety Guarantees

- No approval transition creates `published`, `scheduled`, or `sent`.
- Content draft approval only changes approval status.
- Calendar `ready_for_scheduling` only marks an internal draft as ready; it does not schedule on a platform.
- Community reply approval never sends a reply.
- `ai_community_reply_drafts.auto_reply_allowed` is constrained to `false`.

## Phase 8 Workspace And Brand Brain Routes

Phase 8 adds product workspace and Brand Brain contracts used by the broader AI Social Media Manager dashboard. These routes remain internal and do not publish, schedule, scrape, or send replies.

Routes:

- `GET /internal/ai/workspace-context`
- `GET /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile`
- `PUT /internal/ai/brand-profile/{brand_id}`
- `POST /internal/ai/brand-profile/validate`

Brand profile upsert request:

```json
{
  "profile": {
    "brand_id": "brand-1",
    "brand_name": "ARIA Labs",
    "industry": "Marketing software",
    "description": "Approval-based AI social media management workspace.",
    "products_or_services": ["AI content workspace"],
    "target_audience": ["marketing teams"],
    "tone_of_voice": ["clear", "strategic"],
    "brand_values": ["human control"],
    "forbidden_topics": ["medical advice"],
    "forbidden_words": ["guaranteed"],
    "approved_claims": ["Helps teams review AI-generated social drafts."],
    "competitors": [],
    "platforms": ["linkedin"],
    "visual_style": {},
    "business_goals": ["increase content quality"],
    "language_preferences": ["en"]
  }
}
```

Brand profile response:

```json
{
  "profile": {},
  "validation": {
    "brand_id": "brand-1",
    "completeness_score": 100,
    "is_complete": true,
    "required_fields": ["brand_name", "industry"],
    "missing_required_fields": [],
    "warnings": [],
    "using_default_context": false
  },
  "product_context": {
    "product_name": "ARIA",
    "product_role": "AI Social Media Manager and Brand Manager",
    "default_workflow_mode": "approval_based",
    "supported_capabilities": ["strategy", "content_generation", "approval_workflow"],
    "automation_boundaries": ["no_auto_publish", "no_auto_reply", "no_real_platform_scheduling"]
  },
  "persisted": true
}
```

Missing persistence returns `503`. Missing stored brand profiles return `404`. Brand profile responses do not expose persistence-level fields such as `brand_profile_json`.
