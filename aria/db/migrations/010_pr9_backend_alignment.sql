CREATE TABLE IF NOT EXISTS ai_workspaces (
  workspace_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_workspace_memberships (
  workspace_id TEXT NOT NULL REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  role VARCHAR(32) NOT NULL CHECK (role IN ('agency_admin','brand_manager','content_creator','analyst')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_ai_memberships_user_workspace
  ON ai_workspace_memberships(user_id, workspace_id);

CREATE TABLE IF NOT EXISTS ai_brands (
  brand_id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, brand_id)
);
CREATE INDEX IF NOT EXISTS idx_ai_brands_workspace ON ai_brands(workspace_id);

INSERT INTO ai_workspaces (workspace_id, name)
SELECT brand_id, COALESCE(brand_profile_json->>'brand_name', brand_id)
FROM ai_brand_memory
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO ai_brands (brand_id, workspace_id, name)
SELECT brand_id, brand_id, COALESCE(brand_profile_json->>'brand_name', brand_id)
FROM ai_brand_memory
ON CONFLICT (brand_id) DO NOTHING;

ALTER TABLE ai_brand_memory ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE ai_brand_memory ADD COLUMN IF NOT EXISTS profile_version INTEGER NOT NULL DEFAULT 1;
UPDATE ai_brand_memory SET workspace_id = brand_id WHERE workspace_id IS NULL;
ALTER TABLE ai_brand_memory ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE ai_brand_memory DROP CONSTRAINT IF EXISTS ai_brand_memory_workspace_id_fkey;
ALTER TABLE ai_brand_memory ADD CONSTRAINT ai_brand_memory_workspace_id_fkey
  FOREIGN KEY (workspace_id) REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE;
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_brand_memory_workspace_brand
  ON ai_brand_memory(workspace_id, brand_id);

ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS owner_id TEXT;
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS campaign TEXT;
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS generation_status VARCHAR(32) NOT NULL DEFAULT 'generated';
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS selected_variant_id UUID;
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE ai_content_drafts ADD COLUMN IF NOT EXISTS internal_planned_at TIMESTAMPTZ;
UPDATE ai_content_drafts SET workspace_id = brand_id WHERE workspace_id IS NULL;
ALTER TABLE ai_content_drafts ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE ai_content_drafts DROP CONSTRAINT IF EXISTS ai_content_drafts_workspace_id_fkey;
ALTER TABLE ai_content_drafts ADD CONSTRAINT ai_content_drafts_workspace_id_fkey
  FOREIGN KEY (workspace_id) REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE;
ALTER TABLE ai_content_drafts DROP CONSTRAINT IF EXISTS ai_content_drafts_generation_status_check;
ALTER TABLE ai_content_drafts ADD CONSTRAINT ai_content_drafts_generation_status_check
  CHECK (generation_status IN ('draft','generating','generated','failed'));
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_content_workspace_idempotency
  ON ai_content_drafts(workspace_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_content_workspace_status_created
  ON ai_content_drafts(workspace_id, generation_status, approval_status, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_content_variants (
  variant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id TEXT NOT NULL REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE,
  draft_id UUID NOT NULL REFERENCES ai_content_drafts(draft_id) ON DELETE CASCADE,
  platform VARCHAR(32) NOT NULL,
  variant_order SMALLINT NOT NULL CHECK (variant_order > 0),
  content_text TEXT NOT NULL,
  package_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  scores_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_selected BOOLEAN NOT NULL DEFAULT false,
  provider TEXT,
  model TEXT,
  token_usage_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (draft_id, platform, variant_order)
);
CREATE INDEX IF NOT EXISTS idx_ai_variants_workspace_draft
  ON ai_content_variants(workspace_id, draft_id, platform, variant_order);

ALTER TABLE ai_content_drafts DROP CONSTRAINT IF EXISTS ai_content_drafts_selected_variant_id_fkey;
ALTER TABLE ai_content_drafts ADD CONSTRAINT ai_content_drafts_selected_variant_id_fkey
  FOREIGN KEY (selected_variant_id) REFERENCES ai_content_variants(variant_id) ON DELETE SET NULL;

ALTER TABLE ai_calendar_draft_items ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE ai_calendar_draft_items ADD COLUMN IF NOT EXISTS content_draft_id UUID;
ALTER TABLE ai_calendar_draft_items ADD COLUMN IF NOT EXISTS planned_at TIMESTAMPTZ;
ALTER TABLE ai_calendar_draft_items ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC';
ALTER TABLE ai_calendar_draft_items ADD COLUMN IF NOT EXISTS planning_state VARCHAR(32) NOT NULL DEFAULT 'draft_plan';
UPDATE ai_calendar_draft_items
SET workspace_id = brand_id,
    planned_at = (scheduled_date + scheduled_time) AT TIME ZONE 'UTC'
WHERE workspace_id IS NULL OR planned_at IS NULL;
ALTER TABLE ai_calendar_draft_items ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE ai_calendar_draft_items DROP CONSTRAINT IF EXISTS ai_calendar_workspace_id_fkey;
ALTER TABLE ai_calendar_draft_items ADD CONSTRAINT ai_calendar_workspace_id_fkey
  FOREIGN KEY (workspace_id) REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE;
ALTER TABLE ai_calendar_draft_items DROP CONSTRAINT IF EXISTS ai_calendar_content_draft_id_fkey;
ALTER TABLE ai_calendar_draft_items ADD CONSTRAINT ai_calendar_content_draft_id_fkey
  FOREIGN KEY (content_draft_id) REFERENCES ai_content_drafts(draft_id) ON DELETE SET NULL;
ALTER TABLE ai_calendar_draft_items DROP CONSTRAINT IF EXISTS ai_calendar_planning_state_check;
ALTER TABLE ai_calendar_draft_items ADD CONSTRAINT ai_calendar_planning_state_check
  CHECK (planning_state IN ('draft_plan','awaiting_approval','approved_internal','ready_for_scheduling','externally_scheduled','published','failed','demo'));
CREATE INDEX IF NOT EXISTS idx_ai_calendar_workspace_planned
  ON ai_calendar_draft_items(workspace_id, planned_at, planning_state);

ALTER TABLE ai_community_reply_drafts ADD COLUMN IF NOT EXISTS workspace_id TEXT;
UPDATE ai_community_reply_drafts SET workspace_id = brand_id WHERE workspace_id IS NULL;
ALTER TABLE ai_community_reply_drafts ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE ai_community_reply_drafts DROP CONSTRAINT IF EXISTS ai_community_workspace_id_fkey;
ALTER TABLE ai_community_reply_drafts ADD CONSTRAINT ai_community_workspace_id_fkey
  FOREIGN KEY (workspace_id) REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_ai_community_workspace_status_created
  ON ai_community_reply_drafts(workspace_id, approval_status, created_at DESC);

ALTER TABLE ai_report_drafts ADD COLUMN IF NOT EXISTS workspace_id TEXT;
UPDATE ai_report_drafts SET workspace_id = brand_id WHERE workspace_id IS NULL;
ALTER TABLE ai_report_drafts ALTER COLUMN workspace_id SET NOT NULL;
ALTER TABLE ai_report_drafts DROP CONSTRAINT IF EXISTS ai_reports_workspace_id_fkey;
ALTER TABLE ai_report_drafts ADD CONSTRAINT ai_reports_workspace_id_fkey
  FOREIGN KEY (workspace_id) REFERENCES ai_workspaces(workspace_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_ai_reports_workspace_status_created
  ON ai_report_drafts(workspace_id, approval_status, created_at DESC);

ALTER TABLE ai_approval_audit_events ADD COLUMN IF NOT EXISTS workspace_id TEXT;
ALTER TABLE ai_approval_audit_events ADD COLUMN IF NOT EXISTS actor_user_id TEXT;
ALTER TABLE ai_approval_audit_events ADD COLUMN IF NOT EXISTS actor_role VARCHAR(32);
CREATE INDEX IF NOT EXISTS idx_ai_approval_workspace_created
  ON ai_approval_audit_events(workspace_id, created_at DESC);

ALTER TABLE ai_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_workspace_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_content_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_community_reply_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_report_drafts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE ai_workspaces, ai_workspace_memberships, ai_brands,
  ai_brand_memory, ai_content_drafts, ai_content_variants, ai_quality_reviews,
  ai_calendar_draft_items, ai_community_reply_drafts, ai_report_drafts,
  ai_approval_audit_events FROM anon, authenticated;
