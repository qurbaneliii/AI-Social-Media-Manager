CREATE TABLE media_assets (
  asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(80) NOT NULL,
  s3_key TEXT NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'pending',
  visual_analysis JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
