CREATE TABLE IF NOT EXISTS ai_brand_memory (
  brand_id TEXT PRIMARY KEY,
  brand_profile_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_content_drafts (
  draft_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id TEXT NOT NULL REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE,
  platform VARCHAR(32) NOT NULL,
  content_type VARCHAR(64) NOT NULL,
  topic TEXT NOT NULL,
  content_package_json JSONB NOT NULL,
  approval_status VARCHAR(32) NOT NULL CHECK (approval_status IN ('approved','needs_revision','requires_human_review')),
  quality_scores_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  audit_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  prompt_version VARCHAR(32) NOT NULL,
  model VARCHAR(80) NOT NULL,
  mock_mode BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_content_drafts_brand_created ON ai_content_drafts(brand_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_quality_reviews (
  review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  draft_id UUID REFERENCES ai_content_drafts(draft_id) ON DELETE SET NULL,
  brand_id TEXT NOT NULL REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE,
  approval_status VARCHAR(32) NOT NULL CHECK (approval_status IN ('approved','needs_revision','requires_human_review')),
  quality_scores_json JSONB NOT NULL,
  improvement_notes TEXT[] NOT NULL DEFAULT '{}',
  audit_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  model VARCHAR(80) NOT NULL,
  mock_mode BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_quality_reviews_brand_created ON ai_quality_reviews(brand_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_calendar_draft_items (
  calendar_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id TEXT NOT NULL REFERENCES ai_brand_memory(brand_id) ON DELETE CASCADE,
  platform VARCHAR(32) NOT NULL,
  scheduled_date DATE NOT NULL,
  scheduled_time TIME NOT NULL,
  draft_status VARCHAR(32) NOT NULL DEFAULT 'draft',
  approval_required BOOLEAN NOT NULL DEFAULT true,
  calendar_item_json JSONB NOT NULL,
  audit_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_calendar_drafts_brand_date ON ai_calendar_draft_items(brand_id, scheduled_date, scheduled_time);
