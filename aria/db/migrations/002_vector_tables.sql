CREATE TABLE brand_voice_embeddings (
  embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  profile_version INT NOT NULL,
  text_chunk TEXT NOT NULL,
  embedding vector(3072) NOT NULL,
  language VARCHAR(16) NOT NULL DEFAULT 'en',
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_brand_voice_company ON brand_voice_embeddings(company_id);
CREATE INDEX idx_brand_voice_hnsw ON brand_voice_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE hashtag_embeddings (
  embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(company_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  hashtag VARCHAR(80) NOT NULL,
  context_text TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  engagement_lift NUMERIC(6,4) NOT NULL DEFAULT 0,
  recency_score NUMERIC(6,4) NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_hashtag_emb_company_platform ON hashtag_embeddings(company_id, platform);
CREATE INDEX idx_hashtag_emb_hnsw ON hashtag_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE post_archive_embeddings (
  embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  post_id UUID REFERENCES posts(post_id) ON DELETE SET NULL,
  platform VARCHAR(24) NOT NULL,
  intent VARCHAR(32) NOT NULL,
  text_chunk TEXT NOT NULL,
  embedding vector(3072) NOT NULL,
  performance_percentile NUMERIC(5,2),
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_post_emb_company_platform ON post_archive_embeddings(company_id, platform);
CREATE INDEX idx_post_emb_hnsw ON post_archive_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE audience_profile_embeddings (
  embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  platform VARCHAR(24) NOT NULL,
  segment_label VARCHAR(120) NOT NULL,
  summary_text TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  segment_performance NUMERIC(6,4),
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audience_emb_company_platform ON audience_profile_embeddings(company_id, platform);
CREATE INDEX idx_audience_emb_hnsw ON audience_profile_embeddings USING hnsw (embedding vector_cosine_ops);
