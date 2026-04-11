CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE companies (
  company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(120) NOT NULL,
  industry_vertical VARCHAR(80) NOT NULL,
  target_market JSONB NOT NULL,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  plan_tier VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email CITEXT UNIQUE NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  auth_provider VARCHAR(40) NOT NULL,
  auth_subject VARCHAR(180) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  membership_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  role VARCHAR(32) NOT NULL CHECK (role IN ('agency_admin','brand_manager','content_creator','analyst')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (company_id, user_id)
);

CREATE TABLE brand_profiles (
  profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL UNIQUE REFERENCES companies(company_id) ON DELETE CASCADE,
  brand_positioning_statement TEXT NOT NULL,
  tone_descriptors TEXT[] NOT NULL,
  tone_fingerprint_json JSONB NOT NULL,
  visual_style_json JSONB,
  approved_vocabulary TEXT[] NOT NULL DEFAULT '{}',
  banned_vocabulary TEXT[] NOT NULL DEFAULT '{}',
  profile_version INT NOT NULL DEFAULT 1,
  confidence NUMERIC(4,3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE posts (
  post_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  intent VARCHAR(32) NOT NULL,
  core_message TEXT NOT NULL,
  campaign_tag VARCHAR(100),
  status VARCHAR(24) NOT NULL CHECK (status IN ('draft','generating','generated','scheduled','published','failed')),
  platform_targets TEXT[] NOT NULL,
  context_snapshot_json JSONB,
  generated_package_json JSONB,
  selected_variant_id UUID,
  quality_score NUMERIC(5,2),
  created_by UUID REFERENCES users(user_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_posts_company_status_created ON posts(company_id, status, created_at DESC);

CREATE TABLE post_variants (
  variant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  post_id UUID NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  variant_order SMALLINT NOT NULL CHECK (variant_order BETWEEN 1 AND 3),
  text TEXT NOT NULL,
  char_count INT NOT NULL,
  scores_json JSONB NOT NULL,
  is_selected BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(post_id, platform, variant_order)
);

CREATE TABLE hashtag_library (
  hashtag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(company_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  tag VARCHAR(80) NOT NULL,
  tier VARCHAR(16) NOT NULL CHECK (tier IN ('broad','niche','micro')),
  monthly_volume INT,
  usage_count INT NOT NULL DEFAULT 0,
  avg_engagement_lift NUMERIC(6,4) NOT NULL DEFAULT 0,
  recency_score NUMERIC(6,4) NOT NULL DEFAULT 0,
  banned BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(company_id, platform, tag)
);
CREATE INDEX idx_hashtag_company_platform_perf ON hashtag_library(company_id, platform, avg_engagement_lift DESC);

CREATE TABLE schedules (
  schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  post_id UUID NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  run_at_utc TIMESTAMPTZ NOT NULL,
  status VARCHAR(32) NOT NULL CHECK (status IN ('queued','awaiting_approval','publishing','published','failed','dead_letter')),
  approval_mode VARCHAR(16) NOT NULL CHECK (approval_mode IN ('human','auto')),
  approved_by UUID REFERENCES users(user_id),
  approved_at TIMESTAMPTZ,
  retry_count INT NOT NULL DEFAULT 0,
  max_retries INT NOT NULL DEFAULT 5,
  next_retry_at TIMESTAMPTZ,
  external_post_id VARCHAR(120),
  error_code VARCHAR(64),
  error_message TEXT,
  idempotency_key VARCHAR(128) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(platform, idempotency_key)
);
CREATE INDEX idx_schedules_status_runat ON schedules(status, run_at_utc);

CREATE TABLE platform_credentials (
  credential_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  account_ref VARCHAR(180) NOT NULL,
  access_token_encrypted TEXT NOT NULL,
  refresh_token_encrypted TEXT,
  token_expires_at TIMESTAMPTZ,
  scopes TEXT[] NOT NULL,
  last_refresh_at TIMESTAMPTZ,
  status VARCHAR(24) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(company_id, platform, account_ref)
);

CREATE TABLE performance_metrics (
  metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  post_id UUID REFERENCES posts(post_id) ON DELETE SET NULL,
  platform VARCHAR(24) NOT NULL,
  external_post_id VARCHAR(120),
  impressions BIGINT NOT NULL DEFAULT 0,
  reach BIGINT NOT NULL DEFAULT 0,
  engagement_rate NUMERIC(8,6) NOT NULL DEFAULT 0,
  click_through_rate NUMERIC(8,6) NOT NULL DEFAULT 0,
  saves BIGINT NOT NULL DEFAULT 0,
  shares BIGINT NOT NULL DEFAULT 0,
  follower_growth_delta INT NOT NULL DEFAULT 0,
  posting_timestamp TIMESTAMPTZ NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL,
  source VARCHAR(16) NOT NULL CHECK (source IN ('webhook','pull','manual')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_metrics_company_platform_captured ON performance_metrics(company_id, platform, captured_at DESC);

CREATE TABLE prompt_templates (
  template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  module_name VARCHAR(40) NOT NULL,
  version INT NOT NULL,
  provider VARCHAR(24) NOT NULL,
  model VARCHAR(64) NOT NULL,
  system_prompt TEXT NOT NULL,
  user_prompt_template TEXT NOT NULL,
  schema_json JSONB NOT NULL,
  performance_score NUMERIC(6,4),
  active BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by UUID REFERENCES users(user_id),
  UNIQUE(module_name, version)
);
CREATE INDEX idx_prompt_module_active ON prompt_templates(module_name, active);
