CREATE TABLE import_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  text TEXT NOT NULL,
  raw JSONB,
  import_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
