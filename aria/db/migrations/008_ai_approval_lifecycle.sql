CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

UPDATE ai_content_drafts
SET approval_status = CASE
  WHEN approval_status = 'approved' THEN 'approved'
  WHEN approval_status = 'needs_revision' THEN 'changes_requested'
  WHEN approval_status = 'requires_human_review' THEN 'draft'
  ELSE approval_status
END
WHERE approval_status IN ('approved', 'needs_revision', 'requires_human_review');

ALTER TABLE ai_content_drafts
  DROP CONSTRAINT IF EXISTS ai_content_drafts_approval_status_check;

ALTER TABLE ai_content_drafts
  ADD CONSTRAINT ai_content_drafts_approval_status_check
  CHECK (approval_status IN ('draft', 'in_review', 'approved', 'rejected', 'changes_requested', 'archived'));

CREATE INDEX IF NOT EXISTS idx_ai_content_drafts_brand_status_created
  ON ai_content_drafts(brand_id, approval_status, created_at DESC);

ALTER TABLE ai_quality_reviews
  ADD COLUMN IF NOT EXISTS review_status VARCHAR(32) NOT NULL DEFAULT 'generated';

ALTER TABLE ai_quality_reviews
  DROP CONSTRAINT IF EXISTS ai_quality_reviews_review_status_check;

ALTER TABLE ai_quality_reviews
  ADD CONSTRAINT ai_quality_reviews_review_status_check
  CHECK (review_status IN ('generated', 'reviewed', 'superseded'));

CREATE INDEX IF NOT EXISTS idx_ai_quality_reviews_draft_created
  ON ai_quality_reviews(draft_id, created_at DESC);

ALTER TABLE ai_calendar_draft_items
  ADD COLUMN IF NOT EXISTS approval_status VARCHAR(32) NOT NULL DEFAULT 'draft';

UPDATE ai_calendar_draft_items
SET approval_status = CASE
  WHEN draft_status IN ('draft', 'in_review', 'approved', 'rejected', 'changes_requested', 'ready_for_scheduling', 'archived')
    THEN draft_status
  ELSE 'draft'
END
WHERE approval_status IS NULL OR approval_status = 'draft';

ALTER TABLE ai_calendar_draft_items
  DROP CONSTRAINT IF EXISTS ai_calendar_draft_items_approval_status_check;

ALTER TABLE ai_calendar_draft_items
  ADD CONSTRAINT ai_calendar_draft_items_approval_status_check
  CHECK (approval_status IN ('draft', 'in_review', 'approved', 'rejected', 'changes_requested', 'ready_for_scheduling', 'archived'));

CREATE INDEX IF NOT EXISTS idx_ai_calendar_drafts_brand_status_created
  ON ai_calendar_draft_items(brand_id, approval_status, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_community_reply_drafts (
  reply_draft_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id TEXT NOT NULL REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE,
  original_message_text TEXT NOT NULL,
  sentiment VARCHAR(64) NOT NULL,
  intent VARCHAR(128) NOT NULL,
  urgency VARCHAR(64) NOT NULL,
  toxicity_risk DOUBLE PRECISION NOT NULL CHECK (toxicity_risk >= 0 AND toxicity_risk <= 1),
  crisis_risk DOUBLE PRECISION NOT NULL CHECK (crisis_risk >= 0 AND crisis_risk <= 1),
  suggested_reply TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  requires_human_review BOOLEAN NOT NULL DEFAULT true,
  escalation_reason TEXT,
  auto_reply_allowed BOOLEAN NOT NULL DEFAULT false CHECK (auto_reply_allowed = false),
  approval_status VARCHAR(32) NOT NULL DEFAULT 'draft'
    CHECK (approval_status IN ('draft', 'in_review', 'approved', 'rejected', 'changes_requested', 'escalated', 'archived')),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_community_reply_drafts_brand_status_created
  ON ai_community_reply_drafts(brand_id, approval_status, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_report_drafts (
  report_draft_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id TEXT NOT NULL REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE,
  report_type VARCHAR(80) NOT NULL,
  date_range TEXT NOT NULL DEFAULT '',
  insight_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  recommendations_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  approval_status VARCHAR(32) NOT NULL DEFAULT 'draft'
    CHECK (approval_status IN ('draft', 'in_review', 'approved', 'rejected', 'changes_requested', 'archived')),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_report_drafts_brand_status_created
  ON ai_report_drafts(brand_id, approval_status, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_approval_audit_events (
  event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  object_id TEXT NOT NULL,
  object_type VARCHAR(40) NOT NULL CHECK (object_type IN ('content_draft', 'calendar_draft', 'community_reply', 'report_draft')),
  previous_status VARCHAR(40),
  new_status VARCHAR(40) NOT NULL,
  action VARCHAR(40) NOT NULL,
  reviewer_id TEXT,
  reviewer_role TEXT,
  reason TEXT NOT NULL DEFAULT '',
  requested_changes JSONB NOT NULL DEFAULT '[]'::jsonb,
  decision_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_approval_audit_events_object_created
  ON ai_approval_audit_events(object_type, object_id, created_at ASC);
