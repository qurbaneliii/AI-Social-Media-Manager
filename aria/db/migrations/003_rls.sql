ALTER TABLE post_variants ADD COLUMN IF NOT EXISTS company_id UUID;
UPDATE post_variants pv
SET company_id = p.company_id
FROM posts p
WHERE p.post_id = pv.post_id
  AND pv.company_id IS NULL;

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY companies_tenant_policy ON companies
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY companies_service_policy ON companies
USING (current_setting('app.role', true) = 'service');

ALTER TABLE brand_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY brand_profiles_tenant_policy ON brand_profiles
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY brand_profiles_service_policy ON brand_profiles
USING (current_setting('app.role', true) = 'service');

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY posts_tenant_policy ON posts
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY posts_service_policy ON posts
USING (current_setting('app.role', true) = 'service');

ALTER TABLE post_variants ENABLE ROW LEVEL SECURITY;
CREATE POLICY post_variants_tenant_policy ON post_variants
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY post_variants_service_policy ON post_variants
USING (current_setting('app.role', true) = 'service');

ALTER TABLE hashtag_library ENABLE ROW LEVEL SECURITY;
CREATE POLICY hashtag_library_tenant_policy ON hashtag_library
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY hashtag_library_service_policy ON hashtag_library
USING (current_setting('app.role', true) = 'service');

ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY schedules_tenant_policy ON schedules
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY schedules_service_policy ON schedules
USING (current_setting('app.role', true) = 'service');

ALTER TABLE platform_credentials ENABLE ROW LEVEL SECURITY;
CREATE POLICY platform_credentials_tenant_policy ON platform_credentials
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY platform_credentials_service_policy ON platform_credentials
USING (current_setting('app.role', true) = 'service');

ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY performance_metrics_tenant_policy ON performance_metrics
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY performance_metrics_service_policy ON performance_metrics
USING (current_setting('app.role', true) = 'service');

ALTER TABLE brand_voice_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY brand_voice_embeddings_tenant_policy ON brand_voice_embeddings
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY brand_voice_embeddings_service_policy ON brand_voice_embeddings
USING (current_setting('app.role', true) = 'service');

ALTER TABLE hashtag_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY hashtag_embeddings_tenant_policy ON hashtag_embeddings
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY hashtag_embeddings_service_policy ON hashtag_embeddings
USING (current_setting('app.role', true) = 'service');

ALTER TABLE post_archive_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY post_archive_embeddings_tenant_policy ON post_archive_embeddings
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY post_archive_embeddings_service_policy ON post_archive_embeddings
USING (current_setting('app.role', true) = 'service');

ALTER TABLE audience_profile_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY audience_profile_embeddings_tenant_policy ON audience_profile_embeddings
USING (company_id = current_setting('app.company_id')::uuid);
CREATE POLICY audience_profile_embeddings_service_policy ON audience_profile_embeddings
USING (current_setting('app.role', true) = 'service');
