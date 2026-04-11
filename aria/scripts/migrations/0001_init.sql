-- FILE: packages/db/migrations/0001_init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'membership_role') THEN
    CREATE TYPE membership_role AS ENUM ('owner', 'admin', 'editor', 'viewer');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'post_status') THEN
    CREATE TYPE post_status AS ENUM ('draft', 'generating', 'generated', 'approved', 'scheduled', 'published', 'failed');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'schedule_status') THEN
    CREATE TYPE schedule_status AS ENUM ('queued', 'awaiting_approval', 'approved', 'publishing', 'published', 'failed', 'dead_letter');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approval_mode') THEN
    CREATE TYPE approval_mode AS ENUM ('human', 'auto');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platform_type') THEN
    CREATE TYPE platform_type AS ENUM ('instagram', 'linkedin', 'facebook', 'x', 'tiktok', 'pinterest');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prompt_status') THEN
    CREATE TYPE prompt_status AS ENUM ('active', 'disabled', 'archived');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'metric_source') THEN
    CREATE TYPE metric_source AS ENUM ('webhook', 'pull', 'manual');
  END IF;
END$$;

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name varchar(120) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  email varchar(255) NOT NULL UNIQUE,
  display_name varchar(120) NOT NULL,
  auth0_user_id varchar(255) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE companies (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  name varchar(120) NOT NULL,
  industry_vertical varchar(120) NOT NULL,
  target_market_json jsonb NOT NULL,
  platform_presence_json jsonb NOT NULL,
  posting_frequency_goal_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz NULL
);

CREATE TABLE memberships (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role membership_role NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id, user_id)
);

CREATE TABLE brand_profiles (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  profile_version integer NOT NULL DEFAULT 1,
  brand_positioning_statement varchar(500) NOT NULL,
  tone_of_voice_descriptors text[] NOT NULL,
  competitor_list text[] NOT NULL DEFAULT ARRAY[]::text[],
  primary_cta_types text[] NOT NULL DEFAULT ARRAY[]::text[],
  brand_color_hex_codes text[] NOT NULL DEFAULT ARRAY[]::text[],
  approved_vocabulary_list text[] NOT NULL DEFAULT ARRAY[]::text[],
  banned_vocabulary_list text[] NOT NULL DEFAULT ARRAY[]::text[],
  tone_fingerprint_json jsonb NULL,
  visual_style_json jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id, profile_version)
);

CREATE TABLE competitors (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name varchar(120) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE media_assets (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  s3_key varchar(512) NOT NULL,
  mime_type varchar(120) NOT NULL,
  size_bytes bigint NOT NULL,
  status varchar(50) NOT NULL,
  uploaded_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE media_analysis (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL,
  media_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  ocr_text text NULL,
  palette_json jsonb NOT NULL,
  typography_json jsonb NOT NULL,
  layout_json jsonb NOT NULL,
  style_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE posts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  post_intent varchar(50) NOT NULL,
  core_message varchar(500) NOT NULL,
  target_platforms platform_type[] NOT NULL,
  campaign_tag varchar(120) NULL,
  attached_media_id uuid NULL,
  manual_keywords text[] NOT NULL DEFAULT ARRAY[]::text[],
  urgency_level varchar(20) NOT NULL,
  requested_publish_at timestamptz NULL,
  status post_status NOT NULL DEFAULT 'generating',
  context_snapshot_json jsonb NULL,
  generated_package_json jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE post_variants (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL,
  post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  platform platform_type NOT NULL,
  variant_rank integer NOT NULL,
  caption_text text NOT NULL,
  hashtags text[] NOT NULL DEFAULT ARRAY[]::text[],
  score numeric(6,3) NOT NULL,
  scoring_metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE schedules (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  platform platform_type NOT NULL,
  run_at_utc timestamptz NOT NULL,
  approval_mode approval_mode NOT NULL,
  status schedule_status NOT NULL DEFAULT 'queued',
  retry_count integer NOT NULL DEFAULT 0,
  external_post_id varchar(255) NULL,
  idempotency_key varchar(120) NOT NULL UNIQUE,
  timezone varchar(50) NULL,
  force_window boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id, platform, run_at_utc)
);

CREATE TABLE platform_credentials (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  platform platform_type NOT NULL,
  encrypted_token_ciphertext bytea NOT NULL,
  encrypted_token_iv bytea NOT NULL,
  encrypted_token_tag bytea NOT NULL,
  kms_encrypted_data_key bytea NOT NULL,
  token_expires_at timestamptz NULL,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id, platform)
);

CREATE TABLE prompt_templates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NULL,
  name varchar(120) NOT NULL,
  version integer NOT NULL,
  status prompt_status NOT NULL DEFAULT 'active',
  template_body text NOT NULL,
  variables_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, name, version)
);

CREATE TABLE performance_metrics (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  platform platform_type NOT NULL,
  external_post_id varchar(255) NOT NULL,
  impressions integer NOT NULL,
  reach integer NOT NULL,
  engagement_rate numeric(8,5) NOT NULL,
  click_through_rate numeric(8,5) NOT NULL,
  saves integer NOT NULL,
  shares integer NOT NULL,
  follower_growth_delta integer NOT NULL,
  posting_timestamp timestamptz NOT NULL,
  captured_at timestamptz NOT NULL,
  source metric_source NOT NULL,
  attributes_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE audit_logs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NULL REFERENCES companies(id) ON DELETE SET NULL,
  actor_user_id uuid NULL,
  action varchar(120) NOT NULL,
  resource_type varchar(80) NOT NULL,
  resource_id varchar(255) NOT NULL,
  ip_address varchar(64) NULL,
  user_agent varchar(512) NULL,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE brand_voice_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  source_type varchar(50) NOT NULL,
  source_ref varchar(120) NOT NULL,
  embedding vector(1536) NOT NULL,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE hashtag_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  hashtag varchar(80) NOT NULL,
  embedding vector(1536) NOT NULL,
  performance_weight numeric(8,5) NOT NULL DEFAULT 0,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE post_archive_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  post_id uuid NOT NULL,
  platform platform_type NOT NULL,
  embedding vector(1536) NOT NULL,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audience_profile_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  audience_segment varchar(120) NOT NULL,
  embedding vector(1536) NOT NULL,
  metadata_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE idempotency_keys (
  key varchar(120) PRIMARY KEY,
  tenant_id uuid NOT NULL,
  company_id uuid NOT NULL,
  scope varchar(80) NOT NULL,
  response_json jsonb NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_companies_tenant_id ON companies(tenant_id);
CREATE INDEX idx_memberships_tenant_id ON memberships(tenant_id);
CREATE INDEX idx_memberships_company_id ON memberships(company_id);
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_brand_profiles_tenant_id ON brand_profiles(tenant_id);
CREATE INDEX idx_brand_profiles_company_id ON brand_profiles(company_id);
CREATE INDEX idx_competitors_tenant_id ON competitors(tenant_id);
CREATE INDEX idx_competitors_company_id ON competitors(company_id);
CREATE INDEX idx_media_assets_tenant_id ON media_assets(tenant_id);
CREATE INDEX idx_media_assets_company_id ON media_assets(company_id);
CREATE INDEX idx_media_assets_s3_key ON media_assets(s3_key);
CREATE INDEX idx_media_analysis_tenant_id ON media_analysis(tenant_id);
CREATE INDEX idx_media_analysis_company_id ON media_analysis(company_id);
CREATE INDEX idx_media_analysis_media_id ON media_analysis(media_id);
CREATE INDEX idx_posts_tenant_id ON posts(tenant_id);
CREATE INDEX idx_posts_company_id ON posts(company_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_post_variants_tenant_id ON post_variants(tenant_id);
CREATE INDEX idx_post_variants_company_id ON post_variants(company_id);
CREATE INDEX idx_post_variants_post_id ON post_variants(post_id);
CREATE INDEX idx_post_variants_platform_rank ON post_variants(platform, variant_rank);
CREATE INDEX idx_schedules_tenant_id ON schedules(tenant_id);
CREATE INDEX idx_schedules_company_id ON schedules(company_id);
CREATE INDEX idx_schedules_post_id ON schedules(post_id);
CREATE INDEX idx_schedules_run_status ON schedules(run_at_utc, status);
CREATE INDEX idx_platform_credentials_tenant_id ON platform_credentials(tenant_id);
CREATE INDEX idx_platform_credentials_company_id ON platform_credentials(company_id);
CREATE INDEX idx_prompt_templates_tenant_id ON prompt_templates(tenant_id);
CREATE INDEX idx_prompt_templates_company_id ON prompt_templates(company_id);
CREATE INDEX idx_performance_metrics_tenant_id ON performance_metrics(tenant_id);
CREATE INDEX idx_performance_metrics_company_post_platform ON performance_metrics(company_id, post_id, platform);
CREATE INDEX idx_performance_metrics_captured_at ON performance_metrics(captured_at DESC);
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX idx_audit_logs_action_created_at ON audit_logs(action, created_at DESC);
CREATE INDEX idx_idempotency_keys_tenant_id ON idempotency_keys(tenant_id);
CREATE INDEX idx_idempotency_keys_company_id ON idempotency_keys(company_id);
CREATE INDEX idx_idempotency_keys_expires_at ON idempotency_keys(expires_at);

CREATE INDEX gin_posts_context_snapshot_json ON posts USING gin (context_snapshot_json);
CREATE INDEX gin_posts_generated_package_json ON posts USING gin (generated_package_json);
CREATE INDEX gin_brand_profiles_tone_fingerprint_json ON brand_profiles USING gin (tone_fingerprint_json);
CREATE INDEX gin_brand_profiles_visual_style_json ON brand_profiles USING gin (visual_style_json);
CREATE INDEX gin_platform_credentials_metadata_json ON platform_credentials USING gin (metadata_json);
CREATE INDEX gin_performance_metrics_attributes_json ON performance_metrics USING gin (attributes_json);

CREATE INDEX idx_brand_voice_embeddings_vector ON brand_voice_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_hashtag_embeddings_vector ON hashtag_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_post_archive_embeddings_vector ON post_archive_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_audience_profile_embeddings_vector ON audience_profile_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

SELECT create_hypertable('performance_metrics', by_range('captured_at'), if_not_exists => TRUE);

ALTER TABLE performance_metrics SET (
  timescaledb.compress,
  timescaledb.compress_orderby = 'captured_at DESC',
  timescaledb.compress_segmentby = 'tenant_id,company_id,platform'
);

SELECT add_compression_policy('performance_metrics', INTERVAL '7 days', if_not_exists => TRUE);

CREATE OR REPLACE FUNCTION set_updated_at_column() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_brand_profiles_updated_at BEFORE UPDATE ON brand_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_posts_updated_at BEFORE UPDATE ON posts FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_platform_credentials_updated_at BEFORE UPDATE ON platform_credentials FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_hashtag_embeddings_updated_at BEFORE UPDATE ON hashtag_embeddings FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE TRIGGER trg_audience_profile_embeddings_updated_at BEFORE UPDATE ON audience_profile_embeddings FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();

CREATE OR REPLACE FUNCTION current_tenant_uuid() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid;
$$;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_voice_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE hashtag_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_archive_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audience_profile_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_users ON users USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_companies ON companies USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_memberships ON memberships USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_brand_profiles ON brand_profiles USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_competitors ON competitors USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_media_assets ON media_assets USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_media_analysis ON media_analysis USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_posts ON posts USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_post_variants ON post_variants USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_schedules ON schedules USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_platform_credentials ON platform_credentials USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_prompt_templates ON prompt_templates USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_performance_metrics ON performance_metrics USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_audit_logs ON audit_logs USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_brand_voice_embeddings ON brand_voice_embeddings USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_hashtag_embeddings ON hashtag_embeddings USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_post_archive_embeddings ON post_archive_embeddings USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_audience_profile_embeddings ON audience_profile_embeddings USING (tenant_id = current_tenant_uuid());
CREATE POLICY tenant_isolation_idempotency_keys ON idempotency_keys USING (tenant_id = current_tenant_uuid());

ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE companies FORCE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;
ALTER TABLE brand_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE competitors FORCE ROW LEVEL SECURITY;
ALTER TABLE media_assets FORCE ROW LEVEL SECURITY;
ALTER TABLE media_analysis FORCE ROW LEVEL SECURITY;
ALTER TABLE posts FORCE ROW LEVEL SECURITY;
ALTER TABLE post_variants FORCE ROW LEVEL SECURITY;
ALTER TABLE schedules FORCE ROW LEVEL SECURITY;
ALTER TABLE platform_credentials FORCE ROW LEVEL SECURITY;
ALTER TABLE prompt_templates FORCE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE brand_voice_embeddings FORCE ROW LEVEL SECURITY;
ALTER TABLE hashtag_embeddings FORCE ROW LEVEL SECURITY;
ALTER TABLE post_archive_embeddings FORCE ROW LEVEL SECURITY;
ALTER TABLE audience_profile_embeddings FORCE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys FORCE ROW LEVEL SECURITY;
